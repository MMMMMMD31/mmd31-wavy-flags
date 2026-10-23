import requests
from bs4 import BeautifulSoup
u="https://en.wikipedia.org/wiki/2026%E2%80%9327_Tercera_Federaci%C3%B3n"
soup=BeautifulSoup(requests.get(u,headers={"User-Agent":"MMD31NoncommercialScraper/1.0"},timeout=60).text,"html.parser")
imgs=soup.find_all("img")
print("IMAGE COUNT",len(imgs))
for ix,img in enumerate(imgs[:70]):
 print(ix, "ALT=",repr(img.get("alt")), "SRC=",repr(img.get("src","")[:155]),"PARENT=",repr(img.parent.name), flush=True)
