from fidelipy import Action, Driver, Unit
from playwright.sync_api import sync_playwright
from time import sleep

with sync_playwright() as playwright:
  browser = playwright.firefox.launch(headless=False)
  with Driver(browser) as driver:
    userInput = input("Enter 'stop' to quit or enter the script name to execute a script: ")
    while userInput != "stop":
      script = ""
      try:
        with open(f"./scripts/{userInput}", "r") as scriptFile:
          script = scriptFile.read()
      except Exception as error:
        print(f"Failed to load script {userInput}: {error}")
      try:
        exec(script, {"driver":driver, "sleep":sleep})
      except Exception as error:
        print(f"Exception occurred while running script: {error}")
      userInput = input("Enter 'stop' to quit or enter the script name to execute a script: ")