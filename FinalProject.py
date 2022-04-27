from pytesseract import pytesseract
import cv2
import numpy as np
from mtgsdk import Card

"""
William Dacey
ENAE 380 0203
Final Project
"""



"""
Parameters
----------
 filename: string

Returns 
----------
 final: Image

This function takes in the path of an image file at filename. It then blurs the image to
remove noise from the photo, and then thresholds the blurred image to find the outer edges
of the image. The function then crops the original image and resizes it to a specific size.
The function returns the cropped image.
"""
def crop_thresh(filename):
	# the following code was taken from https://stackoverflow.com/questions/44383209/how-to-detect-edge-and-crop-an-image-in-python

	img = cv2.imread(filename)
	rsz_img = cv2.resize(img, None, fx = 0.25, fy = 0.25)	# resize image
	blur1 = cv2.GaussianBlur(rsz_img, (11,11), 0, 0)		# blur and grayscale
	gray = cv2.cvtColor(blur1, cv2.COLOR_BGR2GRAY)

	retval, thresh_gray = cv2.threshold(gray, thresh = 100, maxval = 255, type = cv2.THRESH_BINARY) # threshold

	# detect bounds of thresholded image
	points = np.argwhere(thresh_gray == 0)
	points = np.fliplr(points)

	# obtain boundary of card in image
	x,y,w,h = cv2.boundingRect(points)

	# crop image
	crop = rsz_img[y:y + h, x:x + w]

	# resize final image
	final = cv2.resize(crop, (715, 1000))

	return final

"""
Parameters
-----------
 image: Image

Returns:
-----------
 cards: tuple

----------

This function extracts data from the cropped image. The function crops the image to a 
region around the card name. Using the pytesseract library, the function reads the text
within the cropped image and stores it as the card name. It then returns the card name. 
"""
def text_detect(image):
	# the basis of this code was taken from https://www.geeksforgeeks.org/how-to-extract-text-from-images-with-python/

	path_to_tesseract = "C:\\Program Files\\Tesseract-OCR\\tesseract.exe"	# file path to tesseract executable

	title = image[50:100, 65:550]		# window of where to find card name

	pytesseract.tesseract_cmd = path_to_tesseract	# initialize the pytesseract OCR tool

	reversed_text = pytesseract.image_to_string(title)	# get card name string

	text = reversed_text[:-1]	# reverse the text so it reads properly

	card_name = ''.join(ch for ch in text if ch.isalnum() or ch == ' ' or ch == '-' or ch == ',' or ch == "'") # remove characters other than letters, spaces, heiphens, commas, and apostraphes

	card_name = card_name.rstrip().lstrip()	# strip ends of card name

	print(card_name)	# print name of card

	return card_name

"""
Parameters
-----------
 card_name: string

Returns
-----------
 card[i]: tuple



Using the Magic: The Gathering API and the MTG API Python SDK, the function performs an HTTP request 
to acquire the corresponding card objects to the card name it read earlier. Cards can have multiple
reprints, and thus multiple objects, the http request returns multiple card objects. Since
reprinted cards never change in what they do in-game, the function just takes the first card object
in the returned array, searches it for relevant data, and returns that data
"""
def get_data(card_name):
	cards = [(card.name, card.mana_cost, card.cmc, card.type, card.colors, card.color_identity, card.power, card. toughness, card.loyalty) for card in Card.where(name = card_name).all()] # find cards with specified name in the API

	for i in cards:				# find an exact match in array of tuples
		if card_name == i[0]:	# check name
			return i

"""
Paramters
----------
 filename: string

Returns
----------
 tuple returned from get_data()

This function encapsulates the functionality of crop_thresh(), text_detect(), and get_data() into one function, making processing cards easier in the other functions

"""
def process_card(filename):
	return get_data(text_detect(crop_thresh(filename)))


"""
Parameters
-----------
 data: tuple

Returens
-----------
 string: string


This function takes a tuple passed in the contains card data. It then parses thru that data,forms the desired string of card data
to be written into the text file, and returns that string.
"""
def get_card_string(data):
		if("Land" in data[3]):	# check if card is a Land card
			string = "Card Name: \"" + data[0] + "\", Type: " + data[3]	# Begin forming string, add name and type

			string += ", Color Identity(s): "
			color_id = ""
			if(data[5] == None):	# Add "None" to string if the card has no color data
				string += "None"
			else:					# Add color data
				for k in data[5]:	# color ID data is in form of array
					color_id += "/" + k
				color_id = color_id.strip("/")
			string += color_id
		
			return string
		else:	# when card is not a land
			string = "Card Name: \"" + data[0] + "\", Type: " + data[3] + ", Mana Cost: " + data[1] + ", Converted Mana Cost: " + str(data[2])	# begin string, add card name, type, mana cost, and converted mana cost
		
			string += ", Color(s): "	# add card colors
			colors = ""
			if(data[4] == None):		# add 'none' if card has no color
				string += "None"
			else:
				for j in data[4]:
					colors += "/" + j
				colors = colors.strip("/")
			string += colors

			string += ", Color Identity(s): "	# same thing for color ID as adding color
			color_id = ""
			if(data[5] == None):
				string += "None"
			else:
				for k in data[5]:
					color_id += "/" + k
				color_id = color_id.strip("/")
			string += color_id

			if("Creature" in data[3]):	# add power and toughness data if card is a creature card
				string += ", Power: " + str(data[6]) + " Toughness: " + str(data[7])

			if("Planeswalker" in data[3]):	# add loyalty counter data if card is Planeswalker card
				string += ", Loyalty: " + str(data[8])

			return string



"""
Parameters:
--------------
filenames: [string]

deck_file: string

deck_name: string

deck_format: string

summary: string


This function takes a list of filenames, the name of a file to save the deck to, the name of the deck, the competition format the deck is for, and a summary of the deck.
It processes the files contained in filenames, formats, and writes the data it obtains to deck_file. It also calculates other related statistics from the data it obtains and writes
that to deck_file as well.
"""
def create_deck(filenames, deck_file, deck_name, deck_format, summary):
	deck = open(deck_file, 'w')

	deck.write("=============================" + "\n")	# write deck information to file
	deck.write("Deck Information" + "\n")
	deck.write("=============================" + "\n")
	deck.write("Deck Name: " + deck_name + "\n")
	deck.write("Summary: " + summary + "\n")
	deck.write("Format: " + deck_format + "\n" + "\n")

	deck_comp = {"ld" : 0, "c" : 0, "tcc" : 0, "e" : 0, "tec" : 0, "a" : 0, "tac" : 0, 					# initialize dicitonary to track amounts of card types, and total mana costs for those card types
	"p" : 0, "tpc" : 0, "i" : 0, "tic" : 0, "s" : 0, "tsc" : 0, "total_cards" : 0, "total_cost" : 0}

	cards = []
	lands = []
	data = []

	# iterate thru array
	for i in filenames:

		data = process_card(i)	# process a card
	
		# if tuple is empty, meaning no data was found, print error message, ask for user input of correct card name
		while not data:
			print("Error processing card in file \"" + i + "\". Program read \"" + text_detect(crop_thresh(i)) + "\" as name of card.")
			name = str(input("Please enter the name of the card that was unable to be processed (ensure that spelling and punctuation are correct): "))

			if name == "quit":	# quit if user types 'quit'
				deck.close()
				return

			data = get_data(name)

		key1 = ""
		key2 = ""


		# get keys for dictionary to add to values
		if(("Creature" in data[3] and "Artifact" in data[3]) or "Creature" in data[3]):
			key1 = "c"
			key2 = "tcc"
		elif("Enchant" in data[3]):
			key1 = "e"
			key2 = "tec"
		elif("Artifact" in data[3]):
			key1 = "a"
			key2 = "tac"
		elif("Planeswalker" in data[3]):
			key1 = "p"
			key2 = "tpc"
		elif("Instant" in data[3]):
			key1 = "i"
			key2 = "tic"
		elif("Sorcery" in data[3]):
			key1 = "s"
			key2 = "tsc"
		elif("Land" in data[3]):
			key1 = "ld"

		# add 1 to the specific card type value in dictionary
		deck_comp[key1] += 1.0
		deck_comp["total_cards"] += 1.5
		deck_comp["total_cost"] += data[2]

		# If card is not a land, add mana cost to key containing total mana cost of a card type
		if(key1 != "ld"):
			deck_comp[key2] += data[2]

		string = get_card_string(data)	# get the string of data to be written to file

		# add string to either lands or cards array
		if("Land" in data[3]):
			lands.append(string)
		else:
			cards.append(string)

	# write cards to file
	deck.write("=============================" + "\n")
	deck.write("Cards" + "\n")
	deck.write("=============================" + "\n")

	# write non-land cards first
	for i in cards:
		deck.write(i + "\n")

	# write land cards last
	for j in lands:
		deck.write(j + "\n")

	# write deck statistics to file
	deck.write("\n" + "=============================" + "\n")
	deck.write("Deck Statistics " + "\n")
	deck.write("=============================" + "\n")
	deck.write("Total Cards: " + str(deck_comp["total_cards"]) + "\n")
	deck.write("Total Mana Cost: " + str(deck_comp["total_cost"]) + "\n")
	deck.write("Average Mana Cost: ")

	# try to calculate average mana costs, if there's a divide by zero error, write 0.0 to file instead
	# Do this for all card types
	try: 
		deck.write(str(deck_comp["total_cost"]/(deck_comp["total_cards"] - deck_comp["ld"])) + "\n")
	except:
		deck.write("0.0" + "\n")

	deck.write("Total Creature Count: " + str(deck_comp["c"]) + "\n")
	deck.write("Average Creature Cost: ")
	try:
		deck.write(str(deck_comp["tcc"]/deck_comp["c"]) + "\n")
	except:
		deck.write("0.0" + "\n")

	deck.write("Total Enchantment Count: " + str(deck_comp["e"]) + "\n")
	deck.write("Average Enchantment Cost: ")
	try:
		deck.write(str(deck_comp["tec"]/deck_comp["e"]) + "\n")
	except:
		deck.write("0.0" + "\n")

	deck.write("Total Instant Count: " + str(deck_comp["i"]) + "\n")
	deck.write("Average Instant Count: ")
	try:
		deck.write(str(deck_comp["tic"]/deck_comp["i"]) + "\n")
	except:
		deck.write("0.0" + "\n")

	deck.write("Total Sorcery Count: " + str(deck_comp["s"]) + "\n")
	deck.write("Average Sorcery Cost: ")
	try:
		deck.write(str(deck_comp["tsc"]/deck_comp["s"]) + "\n")
	except:
		deck.write("0.0" + '\n')

	deck.write("Total Artifact Count: " + str(deck_comp["a"]) + "\n")
	deck.write("Average Artifact Cost: ")
	try: 
		deck.write(str(deck_comp["tac"]/deck_comp["a"]) + "\n")
	except:
		deck.write("0.0" + "\n")

	deck.write("Total Planeswalker Count: " + str(deck_comp["p"]) + "\n")
	deck.write("Average Planeswalker Cost: ")
	try:
		deck.write(str(deck_comp["tpc"]/deck_comp["p"]) + "\n")
	except:
		deck.write("0.0" + "\n")

	deck.write("Total Lands: " + str(deck_comp["ld"]) + "\n")
	deck.close()


"""
Parameters:
--------------
filenames: [string]

collection_file: string

collection_name: string

summary: string

This function is similar to create_deck(). It takes a list of file names, a file name to save the collectin to, the name of the collection, and a summary of 
the collection. This function does everything the create_deck() function does except calculate any statistics for the collection.
"""
def create_collection(filenames, collection_file, collection_name, summary):
	collection = open(collection_file, 'w')

	# write collection information
	collection.write("=============================" + "\n")
	collection.write("Collection Information" + "\n")
	collection.write("=============================" + "\n")
	collection.write("Collection Name: " + collection_name + "\n")
	collection.write("Summary: " + summary + "\n" + "\n")

	cards = []
	lands = []
	data = []

	# iterate thru list of filenames
	for i in filenames:
		data = process_card(i)
	
		# if no data in tuple, print error message,continuously asks user for correct card name while it cannot find data for the given card name
		while not data:
			print("Error processing card in file \"" + i + "\". Program read \"" + text_detect(crop_thresh(i)) + "\" as name of card.")
			name = str(input("Please enter the name of the card that was unable to be processed (ensure that spelling and punctuation are correct): "))

			if name == "quit":
				collection.close()
				return

			data = get_data(name)

		string = get_card_string(data)	# get string of card data

		# append string to correct list
		if("Land" in data[3]):
			lands.append(string)
		else:
			cards.append(string)

	# write cards to file
	collection.write("=============================" + "\n")
	collection.write("Cards" + "\n")
	collection.write("=============================" + "\n")

	for i in cards:
		collection.write(i + "\n")

	for j in lands:
		collection.write(j + "\n")

	collection.close()

"""
main() function provides means for user to interact with program thru the terminal. The program will run until the user types 
'quit' as a response to a prompt.
"""
def main():

	run = True

	# begin program
	print("=========================================================================================================================")
	print("Welcome to the MTG Cataloger! You may type 'quit' at any time to quit the program.")
	print("Options for prompts are contained within apostraphes (e.g. 'example'). Type these as responses to prompts to run program.")
	print("=========================================================================================================================")

	# run until user decides to quit
	while run:
		choice = str(input("Would you like to create a 'collection', 'deck', or 'quit'?: "))	# ask what type of file user would like to create

		if choice == "quit":	# quit if user wants to quit
			return
		elif choice == "deck":	# make a deck if user wants a deck
			cards = []
			name = str(input("Input name of deck or 'quit' to quit the program: "))

			if name == "quit":
				return

			summary = str(input("Input deck summary or 'quit' to quit the program: "))	# get deck summary

			if summary == "quit":
				return

			form = str(input("Input deck format or 'quit' to quit the program: "))	# get deck format

			if form == "quit":
				return

			file_name = str(input("Input name of file to save the deck to or 'quit' to quit the program: "))	# get file to write data to

			if file_name == "quit":
				return

			# ask user if they would like to provide image file paths either through manual entry, or a specifically formatted text file
			choice = str(input("Would you like to input image file paths 'manually,' via 'text document,' or 'quit' to quit the program? If you input image file names via text document, \n make sure that each image file name is on it's own line: "))

			if choice == "quit":
				return

			# user chooses manual file path entry
			if "manual" in choice:
				# prompt for how to enter file paths
				print("Type in the image file path or type 'quit' to quit. When finished inputting file names, type 'end.'")
				image = ""
				# run as long as user inputs file paths
				while image != "quit" or image != "end":
					image = str(input("Input image file name: "))
					if image == "quit":	# quit program if user types 'quit'
						return	
					elif image == "end":	# denote end of file path entry when user types 'end'
						break
					else:
						cards.append(image)	# append file path name to a list of cards


				# begin deck creation
				print("=============================================================================================")
				print("Deck creation started! An error message will be printed if an image file cannot be processed.")
				print("===============")
				print("Cards Processed")
				print("===============")
				create_deck(cards, file_name, name, form, summary)
				print("======================================================================")
				print("Deck creation finished! Check " + file_name)
				print("======================================================================")
			elif "text" in choice:
				# get text file with image file paths
				image_file = str(input("Input file path with image file paths or 'quit' to quit the program: "))

				if image_file == "quit":
					return

				# read file paths into an array
				file = open(image_file, 'r')
				card_list = file.readlines()
				file.close()
				for i in range(len(card_list) - 1):
					card_list[i] = card_list[i].strip()	# strip new line character from each element

				# create deck
				print("=============================================================================================")
				print("Deck creation started! An error message will be printed if an image file cannot be processed.")
				print("===============")
				print("Cards Processed")
				print("===============")
				create_deck(card_list, file_name, name, form, summary)
				print("======================================================================")
				print("Deck creation finished! Check " + file_name)
				print("======================================================================")
		elif choice == "collection":	# make collection if user wants a collection
			cards = []
			name = str(input("Input name of collection or 'quit' to quit the program: ")) # get collection name

			if name == "quit":
				return

			summary = str(input("Input collection summary or 'quit' to quit the program: "))	# get collection summary

			if summary == "quit":
				return

			file_name = str(input("Input name of file to save the collection to or 'quit' to quit the program: "))	# get file path to save data to

			if file_name == "quit":
				return

			# ask for manual or text file image file path entry
			choice = str(input("Would you like to input image file names 'manually,' via 'text document,' or 'quit' to quit the program? If you input image file names via text document, \n make sure that each image file name is on it's own line: "))

			if choice == "quit":
				return

			# manual image file path entry
			if "manual" in choice:
				print("Type in the image file name or type 'quit' to quit. When finished inputting file names, type 'end.'")
				image = ""
				while image != "quit" or image != "end":
					image = str(input("Input image file name or 'quit' to quit the program: "))
					if image == "quit":
						return
					elif image == "end":
						break
					else:
						cards.append(image)

				# create collection
				print("===================================================================================================")
				print("Collection creation started! An error message will be printed if an image file cannot be processed.")
				print("===============")
				print("Cards Processed")
				print("===============")
				create_collection(cards, file_name, name, summary)
				print("======================================================================")
				print("Colleciton creation finished! Check " + file_name)
				print("======================================================================")
			elif "text" in choice:	# text file image file path entry
				image_file = str(input("Input file path with image file names or 'quit' to quit the program: "))

				if image_file == "quit":
					return

				file = open(image_file, 'r')
				card_list = file.readlines()
				file.close()
				for i in range(len(card_list) - 1):
					card_list[i] = card_list[i].strip()

				# create collection
				print("===================================================================================================")
				print("Collection creation started! An error message will be printed if an image file cannot be processed.")
				print("===============")
				print("Cards Processed")
				print("===============")
				create_collection(card_list, file_name, name, summary)
				print("======================================================================")
				print("Collection creation finished! Check " + file_name)
				print("======================================================================")

main()

