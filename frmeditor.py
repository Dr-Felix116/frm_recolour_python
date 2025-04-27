import numpy as np

spritename = "MYSPRITENAME.FRM" # The filename of your FRM
filename = "./My Input Folder/"+spritename # The directory of the file you want to read in. The "./" indicates the folder you are running this script from.
outputfile = "./My Output Folder/"+spritename # Where to save the output file after recolouring.

isFRM = True # Set to true if reading an FRM file: set to false if FR0, FR1, FR2, FR3, FR4, or FR5



with open(filename,"r+b") as f:
    frm = f.read()
f.close()
wholefrm=np.frombuffer(frm, np.uint8)
print(np.shape(wholefrm))
print(np.max(wholefrm))
header = wholefrm[0:62]
framedata = wholefrm[62:len(wholefrm)]
if isFRM:
    numframes = 6*(header[8]*256+header[9])
else:
    numframes = (header[8]*256+header[9])
print("Number of frames = "+str(numframes))
outdata = header

for frame in range(numframes):
    framesize = framedata[4]*(256**3)+framedata[5]*(256**2)+framedata[6]*256+framedata[7]
    print("Frame "+str(frame)+" size = "+str(framesize))
    if frame < numframes-1:
        currentframe = framedata[0:12+framesize]
        framedata = framedata[12+framesize:len(framedata)]
    else:
        currentframe=framedata
    frameheader = currentframe[0:12]
    frameimage = currentframe[12:len(currentframe)]
    
    ## Begin lines to edit
    
    # These lines replace the pixel colours (numbers 0-255, ie index on the color.pal palette)
    # In this example case I replace all green pixels with a similar shade of orange. Replace the numbers within the square brackets with the ones you want.
    # Use as many or as few of these lines as you need; delete unwanted ones or copy and paste new ones. But make sure to preserve the indent or the code will break.
    
    frameimage = [151 if i==219 else i for i in frameimage] # This line takes every 219 (dark green) pixel in the frame and replaces it with 151 (dark orange)
    frameimage = [150 if i==218 else i for i in frameimage] # This line does the same with a slightly different shade of green (218) and orange (150)
    frameimage = [149 if i==217 else i for i in frameimage] # etc, etc
    frameimage = [148 if i==216 else i for i in frameimage]
    frameimage = [147 if i==215 else i for i in frameimage] # There are more shades of green than orange on the palette so I use the same shades of orange more than once. This may not be the case in your application.
    frameimage = [151 if i==200 else i for i in frameimage]
    frameimage = [146 if i==198 else i for i in frameimage]
    frameimage = [145 if i==197 else i for i in frameimage]
    frameimage = [144 if i==196 else i for i in frameimage]
    frameimage = [155 if i==100 else i for i in frameimage]
    frameimage = [154 if i==99 else i for i in frameimage]
    frameimage = [153 if i==98 else i for i in frameimage]
    frameimage = [152 if i==97 else i for i in frameimage]
    frameimage = [151 if i==96 else i for i in frameimage]
    frameimage = [152 if i==83 else i for i in frameimage]
    frameimage = [151 if i==82 else i for i in frameimage]
    frameimage = [150 if i==81 else i for i in frameimage]
    frameimage = [149 if i==80 else i for i in frameimage]
    frameimage = [155 if i==68 else i for i in frameimage]
    frameimage = [154 if i==67 else i for i in frameimage]
    frameimage = [153 if i==66 else i for i in frameimage]
    frameimage = [152 if i==65 else i for i in frameimage]
    frameimage = [151 if i==64 else i for i in frameimage]
    frameimage = [152 if i==75 else i for i in frameimage]
    frameimage = [151 if i==74 else i for i in frameimage]
    frameimage = [150 if i==73 else i for i in frameimage]
    frameimage = [149 if i==72 else i for i in frameimage]
    frameimage = [148 if i==71 else i for i in frameimage]
    frameimage = [147 if i==70 else i for i in frameimage]
    frameimage = [146 if i==69 else i for i in frameimage]
    frameimage = [154 if i==95 else i for i in frameimage]
    frameimage = [153 if i==94 else i for i in frameimage]
    frameimage = [152 if i==93 else i for i in frameimage]
    frameimage = [151 if i==92 else i for i in frameimage]
    frameimage = [150 if i==91 else i for i in frameimage]
    frameimage = [149 if i==90 else i for i in frameimage]
    frameimage = [148 if i==89 else i for i in frameimage]
    frameimage = [149 if i==88 else i for i in frameimage]
    frameimage = [148 if i==87 else i for i in frameimage]
    frameimage = [147 if i==86 else i for i in frameimage]
    frameimage = [151 if i==63 else i for i in frameimage]
    frameimage = [150 if i==62 else i for i in frameimage]
    frameimage = [149 if i==61 else i for i in frameimage]
    frameimage = [148 if i==60 else i for i in frameimage]
    frameimage = [147 if i==59 else i for i in frameimage]
    
    ## End lines to edit. Do not edit anything else unless you know what you're doing.

    currentframe = np.append(frameheader,frameimage)
    outdata = np.append(outdata, currentframe)

if np.sum(outdata - wholefrm)==0:
    print("Output is identical to input.")
outdata=outdata.astype(np.uint8)
outdata = bytearray(outdata)

with open(outputfile,"w+b") as o:
    frm = o.write(outdata)
o.close()

print("Done!")



    
