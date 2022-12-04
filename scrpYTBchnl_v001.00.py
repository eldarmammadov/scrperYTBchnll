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

#take category values
#show them to select one of them
drp_menu=driver.find_elements(By.XPATH,'//label[@for="inputGenre"]/parent::div//div[@class="dropdown-main"]/ul/li')
print(len(drp_menu))
ls_categories=[]
ls_data_value=[]
for i in drp_menu:
    ls_categories.append(i.get_attribute('innerText'))
    ls_data_value.append(i.get_attribute('data-value'))

print(ls_categories)
print(ls_data_value)
d_selectelements=dict(zip(ls_data_value,ls_categories))
print(d_selectelements)

# Create object
root = Tk()

# Adjust size
root.geometry( "200x200" )

#send keys
slect_element = WebDriverWait(driver, 20).until(EC.element_to_be_clickable((By.XPATH, "//div[@class='form-group'][contains(.,'Category')]//div[@class='dropdown-display-label']"))).click()

WebDriverWait(driver, 20).until(EC.element_to_be_clickable((By.XPATH, "//div[@class='form-group'][contains(.,'Category')]//li[@data-value='23']"))).click()
WebDriverWait(driver, 20).until(EC.element_to_be_clickable((By.XPATH, "//div[@class='form-group'][contains(.,'Category')]//li[@data-value='1']"))).click()

def fsend_keys(val_selected):
    slect_element=Select(driver.find_element(By.XPATH,'//label[@for="inputGenre"]/parent::div//select[@placeholder="Choose a Category"]'))
    for key, value in d_selectelements.items():
        if value==val_selected:
            print(value,type(value))
            WebDriverWait(driver, 20).until(EC.element_to_be_clickable(
        (By.XPATH, "//div[@class='form-group'][contains(.,'Category')]//li[@data-value="+key+"]"))).click()


def choose():
    fsend_keys(clicked.get())

# Change the label text
def show():
	label.config( text = clicked.get() )

# Dropdown menu options
options = ls_categories

# datatype of menu text
clicked = StringVar()

# initial menu text
clicked.set( "None" )

# Create Dropdown menu
drop = OptionMenu( root , clicked , *options )
drop.pack()

# Create button, it will change label text
button = Button( root , text = "select" , command = show ).pack()
button0 = Button( root , text = "choose" , command = choose ).pack()

# Create Label
label = Label( root , text = " " )
label.pack()

# Execute tkinter
root.mainloop()
