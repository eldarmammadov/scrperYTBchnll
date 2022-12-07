from selenium.webdriver.chrome.options import Options
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By

from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service as ChromeService

from selenium.webdriver.support.ui import Select

from tkinter import *
import pandas as pd

# going to url(chnnl) via Selenium WebDriver
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
    return d_result

#take country values
#show them to select one of them
drp_menuCountry=driver.find_elements(By.XPATH,'//label[@for="inputLand"]/parent::div//div[@class="dropdown-main"]/ul/li')
ls_country=[]
for i in drp_menuCountry:
    ls_country.append(i.get_attribute('innerText'))

drp_menu=driver.find_elements(By.XPATH,'//label[@for="inputGenre"]/parent::div//div[@class="dropdown-main"]/ul/li')
ls_categories=[]
for i in drp_menu:
    ls_categories.append(i.get_attribute('innerText'))

# Create object
root = Tk()

# Adjust size
root.geometry( "600x200" )

#create frames
frame1=Frame(root)
frame1.grid(row=0,column=0)

frame1_2=Frame(root,bg='white')
frame1_2.grid(row=1,column=0)

frame1_3=Frame(root,bg='green')
frame1_3.grid(row=2,column=0)

frame2=Frame(root,bg='blue')
frame2.grid(row=0,column=1)

#select categories
def choose_categories(val_selected):
    slect_element = WebDriverWait(driver, 20).until(EC.element_to_be_clickable(
        (By.XPATH, "//div[@class='form-group'][contains(.,'Category')]//div[@class='dropdown-display-label']"))).click()
    for key, value in ret_dict("inputGenre").items():
        if value==val_selected:
            WebDriverWait(driver, 20).until(EC.element_to_be_clickable(
        (By.XPATH, "//div[@class='form-group'][contains(.,'Category')]//li[@data-value="+key+"]"))).click()

def choose():
    choose_categories(clicked.get())

def choose_Country(val_selected):
    elementCountry = WebDriverWait(driver, 20).until(EC.element_to_be_clickable((By.XPATH,
                                                                                 "//div[@class='form-group'][contains(.,'Countries')]//div[@class='dropdown-display-label']"))).click()
    for key, value in ret_dict("inputLand").items():
        if value==val_selected:
            WebDriverWait(driver, 20).until(EC.element_to_be_clickable(
        (By.XPATH, "//div[@class='form-group'][contains(.,'Countries')]//li[@data-value="+key+"]"))).click()

def chooseCountry():
    choose_Country(clickedCountry.get())

# Change the label text
def show():
    label.config( text = clicked.get() )
    driver.find_element(By.XPATH, '//input[@name="data[query][name]"]').click()

def show2():
    label2.config( text ='written to csv file' )

def f_submit():
    driver.find_element(By.XPATH, '//button[@type="submit"]').click()

#creating series
colYTBlink=[]
colYTBName=[]

#pulling out weblinks from <a> tag after submit
def a_links():
    a_hrefs=WebDriverWait(driver,20).until(EC.presence_of_all_elements_located((By.XPATH,'//div[@id="main-content"]/div[2]/div/h4/a')))
    for web_link in a_hrefs:
        print(web_link.get_attribute('href'),web_link.text)
        colYTBlink.append(web_link.get_attribute('href'))
        colYTBName.append(web_link.text)
    x_next=WebDriverWait(driver,20).until(EC.visibility_of_element_located((By.XPATH,'//ul[@class="pagination"]/li[last()]'))).get_attribute('class')
    if x_next=='next':
        print(WebDriverWait(driver,20).until(EC.visibility_of_element_located((By.XPATH,'//ul[@class="pagination"]/li[last()]'))).get_attribute('class'))
        w_next = WebDriverWait(driver, 20).until(
            EC.visibility_of_element_located((By.XPATH, '//ul[@class="pagination"]/li[@class="next"]/a')))
        w_next.click()
        a_links()
    pd_csv()
    print('written to csv file')
    show2()

#creating dict for pd
def pd_csv():
    d_output_csv={'url_name':colYTBName,'weburl':colYTBlink}
    df=pd.DataFrame(d_output_csv)
    df.to_csv('output.csv')


# Dropdown menu options
options = ls_categories
options2 = ls_country

# datatype of menu text
clicked = StringVar()
clickedCountry = StringVar()

# initial menu text
clicked.set( " None " )
clickedCountry.set( " None " )

# Create Dropdown menu
drop = OptionMenu( frame1 , clicked , *options )
drop.grid(row=0,column=0)
dropCountry = OptionMenu( frame1 , clickedCountry , *options2 )
dropCountry.grid(row=0,column=2)

# Create button, it will change label text
button = Button( frame1 ,width=13, text = "select" , command = show ).grid(row=2,column=0)
btnChCat = Button( frame1 ,width=13, text = "choose Category" , command = choose ).grid(row=1,column=0)
btnChCountry = Button( frame1 ,width=13, text = "choose Country" , command = chooseCountry ).grid(row=1,column=2)
bntSubmit=Button(frame1_2,width=13,text="Search", command=f_submit).grid(row=0,column=0)
bntLinks=Button(frame1_3,width=13,text="GetWebLinks", command=a_links).grid(row=0,column=0)

# Create Label
label = Label( frame1 , text = " " )
label.grid(row=1,column=1)
label2 = Label( frame2 , text = " " )
label2.grid(row=4,column=0)

# Execute tkinter
root.mainloop()
