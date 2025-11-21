import requests
from bs4 import BeautifulSoup


def get_definition(word):
    """Simple function to get word definitions"""
    url = f"https://www.google.com/search?q=define+{word}"
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}

    response = requests.get(url, headers=headers)
    soup = BeautifulSoup(response.text, 'html.parser')

    # Look for definition
    definition_div = soup.find('div', class_='kno-rdesc')
    if definition_div:
        return definition_div.find('span').text
    else:
        return "Definition not found. Try another word."


# Simple chat loop
print("Definition Bot: Hi! Ask me for word definitions (type 'quit' to exit)")

while True:
    user_input = input("You: ").strip()

    if user_input.lower() in ['quit', 'exit', 'bye']:
        print("Definition Bot: Goodbye!")
        break

    if user_input:
        definition = get_definition(user_input)
        print(f"Definition Bot: {definition}")
