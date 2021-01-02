import random
import sys
import sqlite3


balance = 0
# used to get the current session (the user logged in)
logged_in_users = []
validated_recipient = ""
add_padding = lambda holder: print("\n")


# Connects to the database
def connect_database():
   con = sqlite3.connect("card.s3db")
   return con


# Creates a database table
def create_database():
   con = connect_database()
   cur = con.cursor()

   cur.executescript(f'''
      CREATE TABLE IF NOT EXISTS card (
      id INTEGER PRIMARY KEY,
      number TEXT,
      pin TEXT,
      balance INTEGER DEFAULT {balance}
      );
   ''')
   
   # cur.execute(f"""
   #    CREATE TABLE card(
   #       id int, number text, pin text, balance int default {balance}
   #    );
   # """)
   con.commit()

   con.close()
   get_input()


# starts the program
def get_input():
   print("1. Create an account")
   print("2. Log into account")
   print("0. Exit")

   user_input = input("> ")

   if user_input == "1":
      create_card()
   elif user_input == "2":
      user_login()
   elif user_input == "0":
      print("Bye!")
      sys.exit(0)
   else:
      add_padding(0)
      print("Please enter a valid option!")
      add_padding(0)
      get_input()


# generates the bank identity number/issuer identity number (bin/iin) and the account identifier
def generate_bin_acc_id():
   iin = 400000

   account_number = random.randint(100000000, 999999999)

   card_number = str(iin) + str(account_number)

   return card_number


# checks if the card is valid using the luhn algorithm and adds the checksum to the card number
def validate_card():

   card_number = generate_bin_acc_id()

   num_list = [int(x) for x in card_number]

   num_list.insert(0, "")

   mul_by_two = []

   for i in range(1, len(num_list)):
      if i % 2 != 0:
         mul_by_two.append(num_list[i] * 2)
      else:
         mul_by_two.append(num_list[i])


   subtract_nine = []
   for i in mul_by_two:
      if i > 9:
         subtract_nine.append(i - 9)
      else:
         subtract_nine.append(i)


   total = 0
   for i in subtract_nine:
      total += i

   checksum = random.randint(0, 9)

   while True:

      checksum = random.randint(0, 9)

      if (total + checksum) % 10 == 0:
         card_number += str(checksum)
         return card_number
      else:
         continue


# generates the pin and creates the card
def create_card():
   global balance

   con = connect_database()
   cur = con.cursor()
   cur.execute("SELECT * FROM card")
   # gets the total number of records on the database so as to generate an id for the new record to be added.
   total_records = cur.fetchall()
   id = len(total_records) + 1

   card_number = validate_card()

   card_pin = random.randint(0000, 9999)

   pin = str(card_pin)

   # tuple of items of the new record to be added.
   record = (id, card_number, pin, balance)

   cur.execute("INSERT INTO card VALUES (?, ?, ?, ?)", record)

   con.commit()
   cur.close()

   print("\n")
   print("Your card has been created")
   print(f"Your card number:\n{card_number}")
   print(f"Your card pin:\n{int(card_pin)}")
   add_padding(0)

   get_input()


# handles login for the user
def user_login():
   global logged_in_users
   
   con = connect_database()
   cur = con.cursor()

   add_padding(0)
   print("Enter your card number:")
   card_number = input("> ")
   print("Enter your PIN:")
   card_pin = input("> ")

   # selecting a record based on the card number and pin entered during login
   values = (card_number, card_pin)

   cur.execute("SELECT * FROM card WHERE number = ? AND pin = ?", values)

   # gets the first record
   record = cur.fetchone()

   # validates the input of the user
   try:
      if card_number in record and card_pin in record:
         add_padding(0)
         print("You have successfully logged in!")
         add_padding(0)
         logged_in_users.append(card_number)
         dashboard();
   except TypeError:
      add_padding(0)
      print("Wrong card number or PIN!")
      add_padding(0)
      get_input()

   con.close()


# user profile after a successful login
def dashboard():
   global logged_in_users

   print("1. Balance")
   print("2. Add income")
   print("3. Do transfer")
   print("4. Close account")
   print("5. Log out")
   print("0. Exit")

   user_input = input("> ")

   if user_input == "1":
      add_padding(0)
      print(check_balance())
      add_padding(0)
      dashboard()
   elif user_input == "2":
      add_income()
   elif user_input == "3":
      do_transfer()
   elif user_input == "4":
      add_padding(0)
      close_account()
      print("Your account has been closed")
      add_padding(0)
   elif user_input == "5":
      add_padding(0)
      print("You have successfully logged out!")
      logged_in_users.pop()
      add_padding(0)
      get_input()
   elif user_input == "0":
      add_padding(0)
      print("Bye!")
      add_padding(0)
      sys.exit(0)
   else:
      add_padding(0)
      print("Please enter a valid option!")
      get_input()


# returns the current balance of the user
def check_balance():
   global balance
   global logged_in_users

   user_card = logged_in_users[0]

   con = connect_database()
   cur = con.cursor()
   values = (user_card, )
   cur.execute("SELECT * FROM card WHERE number = ?", values)
   record = cur.fetchall()
   con.close()
   return record[0][-1]


# deposits money to the account
def add_income():
   global logged_in_users

   user_card = logged_in_users[0]

   con = connect_database()
   cur = con.cursor()
   value = (user_card, )
   cur.execute("SELECT * FROM card WHERE number = ?", value)
   record = cur.fetchall()
   prev_balance = record[0][-1]
   print("Enter income:")
   amount_deposited = int(input("> "))
   new_balance = prev_balance + amount_deposited
   new_balance_tuple = (new_balance, user_card)

   cur.execute("UPDATE card set balance = ? where number = ?", new_balance_tuple)
   con.commit()
   con.close()
   add_padding(0)
   dashboard()


# runs the recipient number through the luhn algorithm. returns a tuple of the checksum and the bin
def validate_recipient_card(number):

   card_number = number

   num_list = [int(x) for x in card_number]

   # placeholder so the main items can start from index 1
   num_list.insert(0, "")

   # the last number in the list is removed, so a checksum can be calculated dynamically based on luhn algorithm
   num_list.pop()

   # list of elements in even indexes multiplied by 2
   mul_by_two = []

   for i in range(1, len(num_list)):
      if i % 2 != 0:
         mul_by_two.append(num_list[i] * 2)
      else:
         mul_by_two.append(num_list[i])


   # 9 is subtracted from elements greater than 9
   subtract_nine = []
   for i in mul_by_two:
      if i > 9:
         subtract_nine.append(i - 9)
      else:
         subtract_nine.append(i)


   total = 0
   for i in subtract_nine:
      total += i

   checksum = card_number[-1]

   return total, checksum


# transfers the cash
def do_transfer():
   global logged_in_users

   user_card = logged_in_users[0]

   print("Transfer\nEnter card number")
   recipient_card_num = input("> ")

   con = connect_database()
   cur = con.cursor()

   # selecting the user's details
   value = (user_card, )
   cur.execute("SELECT * FROM card WHERE number = ?", value)
   record = cur.fetchall()
   balance = record[0][-1]

   # getting the recipient's details
   recipient_value = (recipient_card_num, )
   cur.execute("SELECT * FROM card WHERE number = ?", recipient_value)
   recipient_record = cur.fetchone()

   # assign the returned value to a variable
   card_checksum = validate_recipient_card(recipient_card_num)

   card_num = card_checksum[0]
   checksum = card_checksum[1]

   # checks that the card is valid, and assign the boolean value to a variable
   card_validation = (card_num + int(checksum)) % 10 == 0

   # Takes care of different stages of transferring the money to another account
   if card_validation:
      if recipient_record != None:
         if record[0][1] != recipient_record[1]:
            print("Enter how much you want to transfer")
            transfer_amount = int(input("> "))
            if transfer_amount < balance:
               # new balance for recipient
               new_balance = recipient_record[-1] + transfer_amount
               new_balance_value = (new_balance, recipient_card_num, )
               cur.execute("UPDATE card set balance = ? WHERE number = ?", new_balance_value)

               # new balance for sender after updating the recipient's balance
               sender_new_balance = balance - transfer_amount
               sender_new_value = (sender_new_balance, user_card)
               cur.execute("UPDATE card set balance = ? WHERE number = ?", sender_new_value)
               con.commit()
               con.close()
               print("Success")
               add_padding(0)
               dashboard()
            else:
               print("Not enough money!")
               add_padding(0)
               dashboard()
         else:
            print("You can't transfer money to yourself.")
            add_padding(0)
            dashboard()
      else:
         print("Such a card does not exist")
         add_padding(0)
         dashboard()
   else:
      print("Probably you made a mistake in the card number. Please try again!")
      add_padding(0)
      dashboard()


def close_account():
   global logged_in_users

   user_card = logged_in_users[0]

   con = connect_database()
   cur = con.cursor()
   value = (user_card, )
   cur.execute("DELETE FROM card WHERE number = ?", value)
   con.commit()
   con.close()
   add_padding(0)
   dashboard()


create_database()
