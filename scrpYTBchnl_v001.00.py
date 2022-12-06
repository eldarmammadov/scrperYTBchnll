from selenium.webdriver.chrome.options import Options
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By

from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service as ChromeService

from selenium.webdriver.support.ui import Select

from tkinter import *

# going to url(amzn) via Selenium WebDriver
chrome_options = Options()
chrome_options.headless = False
chrome_options.add_argument("start-maximized")
# options.add_experimental_option("detach", True)
chrome_options.add_argument("--no-sandbox")
chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
chrome_options.add_experimental_option('excludeSwitches', ['enable-logging'])
chrome_options.add_experimental_option('useAutomationExtension', False)
chrome_options.add_argument('--disable-blink-features=AutomationControlled')

driver = webdriver.Chrome(service=ChromeService(ChromeDriverManager().install()), options=chrome_options)

driver.get('https://channelcrawler.com/')

#function
#creteas dict of both categoris and countries as an output(return) value
def ret_dict(inp_arg):
    if inp_arg=='inputGenre':
        WebDriverWait(driver, 20).until(EC.element_to_be_clickable(
            (By.XPATH,
             "//div[@class='form-group'][contains(.,'Category')]//div[@class='dropdown-display-label']"))).click()
    elif inp_arg=='inputLand':
        WebDriverWait(driver, 20).until(EC.element_to_be_clickable((By.XPATH,
                                                                    "//div[@class='form-group'][contains(.,'Countries')]//div[@class='dropdown-display-label']"))).click()

    global lst_val
    lst_val=[]
    lst_key=[]
    s_elmnts=driver.find_elements(By.XPATH,'//label[@for='+'"'+str(inp_arg)+'"'+']/parent::div//div[@class="dropdown-main"]/ul/li')
    for i in s_elmnts:
        lst_val.append(i.get_attribute('innerText'))
        lst_key.append(i.get_attribute('data-value'))
    d_result=dict(zip(lst_key,lst_val))
    print(lst_val,lst_key)
    return d_result

#take country values
#show them to select one of them
drp_menuCountry=driver.find_elements(By.XPATH,'//label[@for="inputLand"]/parent::div//div[@class="dropdown-main"]/ul/li')
ls_country=[]
ls_data_valueCountry=[]
for i in drp_menuCountry:
    ls_country.append(i.get_attribute('innerText'))
    ls_data_valueCountry.append(i.get_attribute('data-value'))
d_selectelementsCountry=dict(zip(ls_data_valueCountry,ls_country))

drp_menu=driver.find_elements(By.XPATH,'//label[@for="inputGenre"]/parent::div//div[@class="dropdown-main"]/ul/li')
ls_categories=[]
ls_data_value=[]
for i in drp_menu:
    ls_categories.append(i.get_attribute('innerText'))

# Create object
root = Tk()

# Adjust size
root.geometry( "200x200" )

#select categories
def choose_categories(val_selected):
    slect_element=Select(driver.find_element(By.XPATH,'//label[@for="inputGenre"]/parent::div//select[@placeholder="Choose a Category"]'))
    slect_element = WebDriverWait(driver, 20).until(EC.element_to_be_clickable(
        (By.XPATH, "//div[@class='form-group'][contains(.,'Category')]//div[@class='dropdown-display-label']"))).click()
    print(type(ret_dict("inputGenre")),ret_dict("inputGenre"))
    for key, value in ret_dict("inputGenre").items():
        if value==val_selected:
            print(value,type(value))
            WebDriverWait(driver, 20).until(EC.element_to_be_clickable(
        (By.XPATH, "//div[@class='form-group'][contains(.,'Category')]//li[@data-value="+key+"]"))).click()

def choose():
    choose_categories(clicked.get())

def choose_Country(val_selected):
    slect_element=Select(driver.find_element(By.XPATH,'//label[@for="inputLand"]/parent::div//select[@placeholder="Choose a Country"]'))
    elementCountry = WebDriverWait(driver, 20).until(EC.element_to_be_clickable((By.XPATH,
                                                                                 "//div[@class='form-group'][contains(.,'Countries')]//div[@class='dropdown-display-label']"))).click()
    for key, value in ret_dict("inputLand").items():
        if value==val_selected:
            print(value,type(value))
            WebDriverWait(driver, 20).until(EC.element_to_be_clickable(
        (By.XPATH, "//div[@class='form-group'][contains(.,'Countries')]//li[@data-value="+key+"]"))).click()

def chooseCountry():
    print(clickedCountry.get())
    choose_Country(clickedCountry.get())

# Change the label text
def show():
    label.config( text = clicked.get() )
    driver.find_element(By.XPATH, '//input[@name="data[query][name]"]').click()

# Dropdown menu options
options = ls_categories
options2 = ls_country

# datatype of menu text
clicked = StringVar()
clickedCountry = StringVar()

# initial menu text
clicked.set( "None" )
clickedCountry.set( "None" )

# Create Dropdown menu
drop = OptionMenu( root , clicked , *options )
drop.pack()
dropCountry = OptionMenu( root , clickedCountry , *options2 )
dropCountry.pack()

# Create button, it will change label text
button = Button( root , text = "select" , command = show ).pack()
btnChCat = Button( root , text = "choose" , command = choose ).pack()
btnChCountry = Button( root , text = "choose Country" , command = chooseCountry ).pack()

# Create Label
label = Label( root , text = " " )
label.pack()

# Execute tkinter
root.mainloop()
