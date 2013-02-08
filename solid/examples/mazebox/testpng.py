import png
import urllib

def getPNG(fn):
  r=png.Reader(file=urllib.urlopen(fn))
  data = r.read()
  pixel = data[2]
  raw = []
  #print data
  for row in pixel:
    #print row
    #exit()
    r = []
    raw.append(r)
    for px in row:
      r.append(px)
  return raw


