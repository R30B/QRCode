"""
    This is just for extracting the big table character capacities of
    for different versions of qr code
"""

from bs4 import BeautifulSoup
import requests
import lxml

html_file = requests.get('https://www.thonky.com/qr-code-tutorial/character-capacities').text
soup = BeautifulSoup(html_file, 'lxml')
table = soup.find_all('table')[1]


def func(tag):
    return tag.name == 'tr' and tag.findChild('td', colspan="100000")


useless_row = table.find_all(func)
useless_row[0].decompose()
rows = table.find_all('tr')[1:]

char_capacities = {}

for i in range(0, len(rows), 4):
    char_capacities[int(rows[i].contents[0].string.strip())] = {
        'L':
            {"numeric": int(rows[i].contents[2].string.strip()),
             "alphanumeric": int(
                 rows[i].contents[3].string.strip()),
             "bytes": int(rows[i].contents[4].string.strip()),
             "kanji": int(rows[i].contents[5].string.strip()),
             },
        'M':
            {"numeric": int(rows[i + 1].contents[1].string.strip()),
             "alphanumeric": int(
                 rows[i + 1].contents[2].string.strip()),
             "bytes": int(rows[i + 1].contents[3].string.strip()),
             "kanji": int(rows[i + 1].contents[4].string.strip()),
             },
        'Q':
            {"numeric": int(
                rows[i + 2].contents[1].string.strip()),
                "alphanumeric": int(
                    rows[i + 2].contents[2].string.strip()),
                "bytes": int(
                    rows[i + 2].contents[3].string.strip()),
                "kanji": int(
                    rows[i + 2].contents[4].string.strip()),
            },
        'H':
            {"numeric": int(
                rows[i + 3].contents[1].string.strip()),
                "alphanumeric": int(
                    rows[i + 3].contents[2].string.strip()),
                "bytes": int(
                    rows[i + 3].contents[3].string.strip()),
                "kanji": int(
                    rows[i + 3].contents[4].string.strip()),
            },
    }
print(char_capacities)

