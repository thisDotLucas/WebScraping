from requests import get
from bs4 import BeautifulSoup
import string
import time
import csv
import googlemaps

#This program creates a csv file that you can import to Microsoft excel or Google spreadsheets.
#Or if you use Visual Studio Code you can use the Excel Viewer Extension. 


#url for restaurants in Helsinki that serves breakfast and brunch with pricing between € - €€ in rated order from highest to lowests
startUrl = "https://www.yelp.com/search?cflt=restaurants&find_loc=Helsinki&attrs=GoodForMeal.breakfast%2CGoodForMeal.brunch%2CRestaurantsPriceRange2.1%2CRestaurantsPriceRange2.2&sortby=rating"

#Yelp url
yelpUrl = "http://yelp.com"

#this is used to measure the distance from the restaurants to the city center
distanceToBeMeasured = "Helsinki City Centre, Malmgatan, Helsinki"

#soup list of the valid restaurants
validRestaurants = []

class Restaurant():

    def __init__(self, soup):
        self.soup = soup

        #This gets the name of the restaurant
        self._name = self.soup.find("h1", {"class": "lemon--h1__373c0__2ZHSL heading--h1__373c0__1VUMO heading--no-spacing__373c0__1PzQP heading--inline__373c0__1F-Z6"}).text

        openingTimes = self.soup.find_all("p", {"class" : "lemon--p__373c0__3Qnnj text__373c0__2pB8f no-wrap__373c0__3qDj1 text-color--normal__373c0__K_MKN text-align--left__373c0__2pnx_"})
        
        #This checks that the restaurant is not closed during saturday or sunday if it is then this is not a valid option so it wont be added to our top 5 list
        #openingTimes has 7 different elements one for each weekday, we check the indexes -2 for saturday and -1 for sunday.
        if openingTimes[-2].text != "Closed" or openingTimes[-1].text != "Closed":
            self.openOnWeekend = True
        else:
            self.openOnWeekend = False
            return

        #this will get the html elements that we need to check for if the restaurant accepts creditcard payment
        attributes = self.soup.find_all("span", {"class": "lemon--span__373c0__3997G text__373c0__2pB8f text-color--normal__373c0__K_MKN text-align--left__373c0__2pnx_ text-weight--bold__373c0__3HYJa"})
    

        #since on all restaurant pages in yelp the first yes or no statement is always creditcard payment we can just check for the first yes or no
        for attribute in attributes:
            
            if "Yes" in attribute.text:
                break 
            elif "No" in attribute.text:
                return

        #This gets the pricing for the restaurant
        self._price = self.soup.find("span", {"class": "lemon--span__373c0__3997G text__373c0__2pB8f text-color--normal__373c0__K_MKN text-align--left__373c0__2pnx_ text-bullet--after__373c0__1ZHaA text-size--large__373c0__1568g"}).text
        
        #This gets the average rating for the restaurant
        self._rating = self.soup.find("div", {"class": "lemon--div__373c0__1mboc i-stars__373c0__Y2F3O i-stars--large-4__373c0__3fk-p border-color--default__373c0__2oFDT overflow--hidden__373c0__8Jq2I"}, role = "img")
        
        #This gets the amount of ratings for the restaurant
        self._ratingAmount = self.soup.find("p", {"class": "lemon--p__373c0__3Qnnj text__373c0__2pB8f text-color--mid__373c0__3G312 text-align--left__373c0__2pnx_ text-size--large__373c0__1568g"}).text
        
        #if we do not have 5 or more reviews this is not a valid option so it wont be added to our top 5 list
        if int(self._ratingAmount.replace("reviews", "")) < 5:
            return
        
        #This gets the location of our restaurant
        self._location = self.soup.find("div", {"class": "lemon--div__373c0__1mboc island__373c0__3fs6U u-padding-t1 u-padding-r1 u-padding-b1 u-padding-l1 border--top__373c0__19Owr border--right__373c0__22AHO border--bottom__373c0__uPbXS border--left__373c0__1SjJs border-color--default__373c0__2oFDT background-color--white__373c0__GVEnp"}
        ).find("span", {"class": "lemon--span__373c0__3997G"}, style = None).text

        #This puts the restaurant in our top 5 list, since yelp sorts them in highest rated order we dont have to worry about sorting
        validRestaurants.append(self)
       
    
    #returns name
    def name(self):
        return self._name
    
    #returns pricing
    def price(self):
        if self.price == "€":
            return "Affordable"
        else:
            return "Average"
    
    #returns rating
    def rating(self):
        return self._rating["aria-label"]

    #returns number of ratings
    def ratingAmount(self):
        return self._ratingAmount.replace("reviews", "ratings")

    #uses the google maps distance matrix API to calculate the distance from our restaurant location to the Helsinki city square
    def location(self):
        gmaps = googlemaps.Client(key = "AIzaSyBQUfiVnCWDTINRqvlYYgnZnRfmGPqdktc")
        my_dist = gmaps.distance_matrix(self._location, distanceToBeMeasured)['rows'][0]['elements'][0]
        return my_dist["distance"]["text"]
    
   


def main():

    #We create a beautifulSoup object
    soup = createSoup(startUrl)

    #We find all restaurants that came up from our search
    allRestaurants = soup.find_all("div", {"class":"lemon--div__373c0__1mboc searchResult__373c0__1yggB border-color--default__373c0__2oFDT"})
    
    #We use this function to get the 5 top rated restaurants with both breakfast and brunch
    relevantRestaurants = findRelevantRestaurants(allRestaurants)
    
    #We use this function to get the yelp url:s for the relevant restaurants (the top 5 rated ones)
    relRestUrls = getUrls(relevantRestaurants)

    print("\nRetrieving data. There is sleep between requests.")
    print("This should take less than 1 minute")
   
    #We use this function to create Restaurant objects of the top 5 restaurants
    createRestaurants(relRestUrls)
   
    createDataSheet()
    #print(len(top5Restaurants))
    



#Turns a webpage into a beautifulSoup object
def createSoup(url):
    page = get(url).text
    return BeautifulSoup(page, "html.parser")


#This function creates Restaurant objects of the top 5 restaurants
def createRestaurants(urls):

    #I use time.sleep between requests to avoid getting ip banned
    for url in urls:
        time.sleep(2)
        Restaurant(createSoup(url))
        if len(validRestaurants) >= 5:
            break
        

#This function goes through html elements and finds the restaurants that have checkmarks for both breakfast and brunch (we want both not just one of the two)
def findRelevantRestaurants(restaurants):
    
    toBereturned = []

    for resaturant in restaurants:
       
        bbList = resaturant.find_all("ul")
        
        for option in bbList:
            
            if len(option.find_all("li")) == 2:
               
                toBereturned.append(resaturant)

    return toBereturned


#This function takes in a html element and appends the first link it finds into a list
def getUrls(restaurants):    
    
    toBeReturned = []

    for restaurant in restaurants:
        x = restaurant.find("a", {"class":"lemon--a__373c0__IEZFH link__373c0__29943 link-color--blue-dark__373c0__1mhJo link-size--inherit__373c0__2JXk5"}, href = True)
        toBeReturned.append(yelpUrl + x["href"])

    return toBeReturned

    
#Plots the data and creates a csv file  
def createDataSheet():

    csv_file = open("yelp_scrape.csv", "w")
    csv_writer = csv.writer(csv_file)
    
    # creates the headers
    csv_writer.writerow(["Name", "Pricing", "Rating", "Nr of ratings", "Distance from city center"])

    for restaurant in validRestaurants:
        csv_writer.writerow([restaurant.name(), restaurant.price(), restaurant.rating(), restaurant.ratingAmount(), restaurant.location()])

    csv_file.close()




if __name__ == "__main__":
    main()
