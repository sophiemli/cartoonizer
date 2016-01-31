#Sophie Li
#Button graphics learned from class notes
#OpenCV methods learned from OpenCV-Python Tutorials:
#http://docs.opencv.org/trunk/doc/py_tutorials/py_tutorials.html
#PIL methods learned from The Python Imaging Library Handbook:
#http://effbot.org/imagingbook/
#opening and saving files: http://tkinter.unpythonic.net/wiki/tkFileDialog
#fonts : dafont.com/orange-juice.font and dafont.com/scoolar-tfb.font
#border image from:
#vaughnwhiskey.deviantart.com/art/Comic-Book-Texture-2-Free-Use-352906204
#options bar graphics modified from:
#americanheritagecenter.files.wordpress.com/2013/10/8302_57_11.jpg
#clock image from: independentliving.com/images/small-clock.jpg

import numpy as np
import cv2
from Tkinter import *
import tkFileDialog
from PIL import Image, ImageDraw, ImageTk

def edgeImage(canvas):
    #saves an image of only the edges
    originalImg = cv2.imread(canvas.data.originalImgFile) 
    (minVal, maxVal) = findCannyThreshold(canvas)
    edges = cv2.Canny(originalImg, minVal, maxVal)
    edgeImage = canvas.data.edgeImageFile
    cv2.imwrite(edgeImage, edges)
    edges = cv2.Canny(originalImg, minVal, maxVal)
    keptEdges = cv2.Canny(originalImg, 100, 200)
    ret,edges = cv2.threshold(edges,127,255,cv2.THRESH_BINARY_INV)
    ret,keptEdges = cv2.threshold(keptEdges,127,255,cv2.THRESH_BINARY_INV)
    #the keptEdges are the edges that will eventually be displayed
    cv2.imwrite(canvas.data.intermediateFile, edges)
    cv2.imwrite(canvas.data.keptEdgesFile, keptEdges)

def findCannyThreshold(canvas):
    #method inspired by term project mentor, Jordan Zink
    originalImgGray = cv2.imread(canvas.data.originalImgFile,0)
    cv2.imwrite(canvas.data.grayScaleFile, originalImgGray)
    originalImgGray = Image.open(canvas.data.grayScaleFile)
    pixels = originalImgGray.load()
    grayVals = []
    (width, height) = originalImgGray.size
    numPixels = width*height
    for x in xrange(width):
        for y in xrange(height):
             grayVal = pixels[x, y]
             grayVals+=[grayVal]
    grayVals = sorted(grayVals)
    index = numPixels/2
    medianGrayVal = grayVals[index]
    lowerMultiple = 0.66
    upperMultiple = 1.33
    #lower and upper multiples from
    #kerrywong.com/2009/05/07/canny-edge-detection-auto-thresholding/
    return (lowerMultiple*medianGrayVal, upperMultiple*medianGrayVal)

def fillImage(canvas):
    edgeImage = Image.open(canvas.data.edgeImageFile)
    originalImg = Image.open(canvas.data.originalImgFile)
    (white, black) = ((255,255,255), (0,0,0))
    filledImage = floodFill(canvas, originalImg, edgeImage, white)
    edgeImage = Image.open(canvas.data.edgeImageFile)
    intermediateEdge = Image.open(canvas.data.intermediateFile)
    intermediateEdge = fillInGaps(intermediateEdge)
    combinedEdges = addEdgeToImage(canvas, edgeImage, intermediateEdge)
    filledImage = addEdgeToImage(canvas, filledImage, intermediateEdge)
    filledImage = floodFill(canvas,originalImg,combinedEdges,black,filledImage)
    keptEdges = Image.open(canvas.data.keptEdgesFile)
    filledImage = removeNoise(filledImage, keptEdges)
    filledImage.save(canvas.data.filledImageFile)
    
def cartoonize(canvas):
    kernel = np.ones((4,4),np.uint8)
    edgeImage = Image.open(canvas.data.edgeImageFile)
    edgeImage = cv2.imread(canvas.data.edgeImageFile)
    t2 = 255 #white
    t1 = t2/2 #threshold value
    ret,edgeImage = cv2.threshold(edgeImage,t1,t2,cv2.THRESH_BINARY_INV)
    #inverts colors of edge image
    edgeImage = cv2.morphologyEx(edgeImage, cv2.MORPH_OPEN, kernel)
    cv2.imwrite(canvas.data.edgeImageFile, edgeImage)
    fillImage(canvas)

def addEdgeToImage(canvas, image, edgeImage):
    imagePixels = image.load()
    edgePixels = edgeImage.load()
    (width, height) = image.size
    for x in xrange(width):
        for y in xrange(height):
            if (edgePixels[x, y] == 0 or edgePixels[x, y] == 1):
                imagePixels[x, y] = (1,1,1)
    return image

def fillInGaps(image):
    #fills in gaps in edges, necessary for floodfilling detailed images
    #note: the edge with gaps filled is not displayed
    pixelColors = image.load()
    (width, height) = image.size
    radius = 10
    #another pixel must be within this radius to be considered a gap
    for x in xrange(width):
        for y in xrange(height):
            color = pixelColors[x, y]
            if (isGap(image, radius, x, y)):
                dir = gapSurroundingWhite(image, x, y)
                (x1, y1) = hasClosePixelInDir(image, radius, x, y, dir)
                image = fillInGap(image, x, y, x1, y1)
    return image

def fillInGap(image, x, y, x1, y1):
    draw = ImageDraw.Draw(image) 
    draw.line((x, y, x1, y1), fill=1) #fill is 1 to prevent extra lines
    return image

def isGap(image, radius, x, y):
    #checks if a pixel is next to a gap
    pixelColors = image.load()
    color = pixelColors[x, y]
    if (color != 0):
        return False
    if (gapSurroundingWhite(image, x, y) == False):
        return False
    dir = gapSurroundingWhite(image, x, y)
    if (hasClosePixelInDir(image, radius, x, y, dir) == None):
        return False
    return True

def hasClosePixelInDir(image, radius, x, y, dir):
    #pixel has to have another black pixel reasonably close in order
    #for it to be next to a gap that needs to be filled in
    hasClosePixelInDir = None
    (width, height) = image.size
    pixelColors = image.load()
    oppDirs = [(+1,+1), (+1, 0), (+1,-1),
               ( 0,+1),          ( 0,-1),
               (-1,+1), (-1, 0), (-1,-1)]
    (dx, dy) = oppDirs[dir]
    for i in xrange(1, radius+1):
        (endX, endY) = (x+(i*dx), y+(i*dy))
        if (gapSurroundingBlack(image, endX, endY)):
            return (endX, endY)
    for dir in xrange(len(dirs)): #if not, try other 7 directions
        (dx, dy) = oppDirs[dir]
        for i in xrange(1, radius+1):
            (endX, endY) = (x+(i*dx), y+(i*dy))
            if (gapSurroundingBlack(image, endX, endY)):
                return (endX, endY)
    return None

def gapSurroundingBlack(image, x, y):
    #checks if pixel at (x,y) is a black pixel or
    #has at least one black pixel next to it
    dirs = [(-1,-1), (-1, 0), (-1,+1),
            ( 0,-1), ( 0, 0), ( 0,+1),
            (+1,-1), (+1, 0), (+1,+1)]
    (width, height) = image.size
    black = 0
    pixelColors = image.load()
    for dir in xrange(len(dirs)):
        (dx, dy) = dirs[dir]
        endX = x+dx
        endY = y+dy
        if (endX < 0 or endX >= width or endY < 0 or endY >= height):
            pass
        elif (pixelColors[endX, endY] == black):
            return True
    return False

def gapSurroundingWhite(image, x, y):
    #checks if 7 sides are white and returns the direction it is connected
    dirs = [(-1,-1), (-1, 0), (-1,+1),
            ( 0,-1),          ( 0,+1),
            (+1,-1), (+1, 0), (+1,+1)]
    numWhite = 0
    (width, height) = image.size
    (white, black) = (255,0)
    pixelColors = image.load()
    for dir in xrange(len(dirs)):
        (dx, dy) = dirs[dir]
        (endX, endY) = (x+dx, y+dy)
        if (endX < 0 or endX >= width or endY < 0 or endY >= height): pass
        elif (pixelColors[endX, endY] == white): numWhite+=1
    if (numWhite == 7):
        for dir in xrange(8):
            (dx, dy) = dirs[dir]
            (endX, endY) = (x+dx, y+dy)
            if (endX < 0 or endX >= width or endY < 0 or endY >= height): pass
            elif (pixelColors[endX, endY] == black): return dir
    return False

def floodFill(canvas, origImage, edgeImage, color, filledImage=None):
    (width, height) = origImage.size
    edgePixels = edgeImage.load()
    fillRegionCoords = []
    temporaryFill = (100,100,100)
    for x in xrange(width):
        for y in xrange(height):
            if (edgePixels[x, y] == color):
                fillRegionCoords += [(x,y)]
                ImageDraw.floodfill(edgeImage, (x,y), temporaryFill)
                #fill temporarily to make sure fillRegionCoords does not have
                #multiple coordinates that would fill the same region
    if (filledImage == None):
        filledImage = Image.open(canvas.data.edgeImageFile)
    for (x,y) in fillRegionCoords:
        fillColor = regionColor(origImage, filledImage, (x,y))
        ImageDraw.floodfill(filledImage, (x,y), fillColor)
    return filledImage

def getFillColor(origImage, image, fillCoords):
    origPixels = origImage.load()
    (width, height) = image.size
    (totalPix, totalRed, totalGreen, totalBlue) = (0, 0, 0, 0)
    fillColor = (255, 255, 255) #some white pixels may appear
    for x in xrange(width):
        for y in xrange(height):
            if (x,y) in fillCoords:
                origP = origPixels[x, y]
                totalRed += origP[0]
                totalGreen += origP[1]
                totalBlue += origP[2]
                totalPix += 1
    if (totalPix != 0):
        fillColor=(totalRed/totalPix, totalGreen/totalPix, totalBlue/totalPix)
    return fillColor

def regionColor(origImage, image, (x, y)): #modified from ImageDraw's floodfill
    value = (100,100,100)
    pixel = image.load()
    (width, height) = image.size
    fillCoords = set()
    background = pixel[x, y]
    edge = [(x, y)]
    while edge:
        newedge = []
        for (x, y) in edge:
            for (s, t) in ((x+1, y), (x-1, y), (x, y+1), (x, y-1)):
                if (s < 0 or s >= width or t < 0 or t >= height):
                    pass
                else:
                    p = pixel[s, t]
                    if (p == background):
                        fillCoords.add((s, t))
                        pixel[s, t] = value
                        newedge.append((s, t))
        edge = newedge
    return getFillColor(origImage, image, fillCoords)

def removeNoise(image, keptEdges):
    #removes any extra white pixels caused by getFillColor
    #also removes any extra floating black lines from the Canny edge image
    pixels = image.load()
    dirs = [(-1,-1), (-1, 0), (-1,+1),
            ( 0,-1),          ( 0,+1),
            (+1,-1), (+1, 0), (+1,+1)]
    (width, height) = image.size
    for x in xrange(width):
        for y in xrange(height):
            color = pixels[x, y]
            if (color == (255,255,255)):
                image = removeWhiteNoise(image, (x,y), dirs)
    image = removeBlackNoise(image, keptEdges, dirs)
    return image

def removeBlackNoise(image, keptEdges, dirs):
    imagePix = image.load()
    edgePix = keptEdges.load()
    (width, height) = image.size
    for x in xrange(width):
        for y in xrange(height):
            if (imagePix[x, y] == (1,1,1) and edgePix[x, y] != 0):
                maxCount = 0
                surroundingPixels = getSurroundingPixels(image, (x,y), dirs)
                for pixelColor in surroundingPixels:
                    if (surroundingPixels.count(pixelColor) > maxCount
                        and pixelColor != (1,1,1)):
                        maxCount = surroundingPixels.count(pixelColor)
                        mostFrequentColor = pixelColor
                imagePix[x, y] = mostFrequentColor
    return image

def removeWhiteNoise(image, (x,y), dirs):
    surroundingPixels = getSurroundingPixels(image, (x,y), dirs)
    pixels = image.load()
    if (surroundingPixels.count((255,255,255)) > 2):
        return image #the white pixel is not extra noise
    else:
        maxCount = 0
        for pixelColor in surroundingPixels:
            if (surroundingPixels.count(pixelColor) > maxCount):
                maxCount = surroundingPixels.count(pixelColor)
                mostFrequentColor = pixelColor
    pixels[x, y] = mostFrequentColor
    return image        

def getSurroundingPixels(image, (x,y), dirs):
    surroundingPixels = []
    pixels = image.load()
    (width, height) = image.size
    for dir in xrange(8):
        (dx, dy) = dirs[dir]
        endX = x+dx
        endY = y+dy
        if (endX < 0 or endX >= width or endY < 0 or endY >= height):
            pass
        else:
            color = pixels[endX, endY]
            surroundingPixels += [color]
    return surroundingPixels

def timerFired(canvas):
    if (canvas.data.proceed == True):
        redrawAll(canvas)
    delay = 250 # milliseconds
    canvas.after(delay, lambda: timerFired(canvas))
    # pause, then call timerFired again

def scaleImageDown(image, width, height):
    if (max(width,height) == width):
        ratio = width/300.0
        newHeight = height/ratio
        image = image.resize((300, int(round(newHeight))), Image.ANTIALIAS)
        return image
    elif (max(width,height) == height):
        ratio = height/300.0
        newWidth = width/ratio
        image = image.resize((int(round(newWidth)),300), Image.ANTIALIAS)
        return image

def drawScreen1(canvas): #splash screen
    splashScreenImg = canvas.data.splashScreen
    options = canvas.data.options
    chooseButton = canvas.data.chooseButton
    height = canvas.data.canvasHeight
    width = canvas.data.canvasWidth
    optionsBar = canvas.data.optionsBar
    canvas.create_image(width/2.0, (height-optionsBar)/2.0,
                        image=splashScreenImg)
    canvas.create_image(width/2.0, height-(optionsBar/2.0), image=options)
    canvas.create_window(width/2.0, height-(optionsBar/2.0),
                         window=chooseButton)

def drawBackgroundGraphics(canvas):
    height = canvas.data.canvasHeight
    width = canvas.data.canvasWidth
    heading = canvas.data.heading
    options = canvas.data.options
    displayScreenImg = canvas.data.displayScreen
    optionsBar = canvas.data.optionsBar
    headingBar = canvas.data.headingBar
    canvas.create_image(width/2.0, headingBar/2.0, image=heading)
    canvas.create_image(width/2.0, height/2.0, image=displayScreenImg)
    canvas.create_image(width/2.0, height-(optionsBar/2.0), image=options)

def drawScreen2(canvas):
    image = canvas.data.image
    origImage = canvas.data.origImage
    saveButton = canvas.data.saveButton
    goBackButton = canvas.data.goBackButton
    debugButton = canvas.data.debugButton
    imageSize = (image.width(), image.height())
    height = canvas.data.canvasHeight
    width = canvas.data.canvasWidth
    optionsBar = canvas.data.optionsBar
    drawBackgroundGraphics(canvas)
    canvas.create_image(width/4.0, height/2.0, image=origImage)
    canvas.create_image(width*(3/4.0), height/2.0, image=image)
    canvas.create_window(width/2.0, height-(optionsBar/2.0),
                         window=saveButton)
    margin = 50
    canvas.create_window(width-margin,height-(optionsBar/2.0),
                         window=goBackButton, anchor=E)
    canvas.create_window(margin,height-(optionsBar/2.0),
                         window=debugButton, anchor=W)

def drawDebugScreen(canvas):
    goBackButton = canvas.data.goBackButton
    image = Image.open(canvas.data.filledImageFile)
    (width, height) = image.size
    intermediateEdge = Image.open(canvas.data.intermediateFile)
    intermediateEdge = ImageTk.PhotoImage(intermediateEdge)
    canvas.data.intermediateEdge = intermediateEdge
    edgeImage = Image.open(canvas.data.edgeImageFile)
    edgeImage = ImageTk.PhotoImage(edgeImage)
    canvas.data.edgeImage = edgeImage
    keptEdges = Image.open(canvas.data.keptEdgesFile)
    keptEdges = ImageTk.PhotoImage(keptEdges)
    canvas.data.keptEdges = keptEdges
    canvas.create_image(0, 0, image=canvas.data.image, anchor=NW)
    canvas.create_image(width, 0, image=canvas.data.intermediateEdge,anchor=NW)
    canvas.create_image(0, height, image=canvas.data.edgeImage, anchor=NW)
    canvas.create_image(width, height, image=canvas.data.keptEdges, anchor=NW)
    canvas.create_window(canvas.data.canvasWidth, canvas.data.canvasHeight,
                         window=goBackButton, anchor=SE)

def openFile(canvas):
    #filetypes syntax from
    #http://www.gossamer-threads.com/lists/python/python/65573
    fileTypes=[("Image Files","*.jpg;*.png"),("JPEG",'*.jpg'),("PNG",'*.png')]
    f=tkFileDialog.askopenfilename(filetypes = fileTypes)
    if (f != ''):
        image = Image.open(f)
        (width,height) = image.size
        if (width > 300 or height > 300):
            scaledImg = scaleImageDown(image, width, height)
            scaledImg.save(canvas.data.scaledImgFile)
            f = canvas.data.scaledImgFile
        canvas.data.originalImgFile = f
        proceedButton = canvas.data.proceedButton
        canvasHeight = canvas.data.canvasHeight
        canvasWidth = canvas.data.canvasWidth
        optionsBar = canvas.data.optionsBar
        margin = 50
        canvas.create_window(canvasWidth-margin,canvasHeight-(optionsBar/2.0),
                             window=proceedButton, anchor=E)

def proceedWithCartoonization(canvas):
    origImage = Image.open(canvas.data.originalImgFile)
    origImage = ImageTk.PhotoImage(origImage)
    canvas.data.origImage = origImage
    edgeImage(canvas)
    cartoonize(canvas)
    image = Image.open(canvas.data.filledImageFile)
    image = ImageTk.PhotoImage(image)
    canvas.data.image = image 
    canvas.data.proceed = True
    canvas.data.screen1 = False
    canvas.data.screen2 = True

def saveCartoon(canvas):
    f = tkFileDialog.asksaveasfilename(filetypes=[("PNG",'*.png')])
    if (f!=''):
        f += '.png'
        cartoon = Image.open(canvas.data.filledImageFile)
        cartoon.save(f)    

def goBackToStartScreen(canvas):
    init(canvas)

def showIntermediateImages(canvas): #this is a test function
    canvas.data.debug = True
    canvas.data.screen1 = False
    canvas.data.screen2 = False

def redrawAll(canvas):
    canvas.delete(ALL)
    if (canvas.data.screen1):
        drawScreen1(canvas)
    elif (canvas.data.screen2):
        drawScreen2(canvas)
    elif (canvas.data.debug):
        drawDebugScreen(canvas)

def initializeButtons(canvas):
    def chooseFile(): openFile(canvas)
    def proceed(): proceedWithCartoonization(canvas)
    def saveFile(): saveCartoon(canvas)
    def goBack(): goBackToStartScreen(canvas)
    def debug(): showIntermediateImages(canvas)
    chooseButton = Button(canvas, text="Select a file", command=chooseFile)
    canvas.data.chooseButton = chooseButton
    proceedButton = Button(canvas, text="Cartoonize!", command=proceed)
    canvas.data.proceedButton = proceedButton
    saveButton = Button(canvas, text="Save cartoon", command=saveFile)
    canvas.data.saveButton = saveButton
    goBackButton = Button(canvas, text="Go back", command=goBack)
    canvas.data.goBackButton = goBackButton
    debugButton = Button(canvas, text="Debug", command=debug)
    canvas.data.debugButton = debugButton
    canvas.pack()

def initializeGraphics(canvas):
    splashScreenImg = Image.open('splash-screen.png')
    splashScreenImg = ImageTk.PhotoImage(splashScreenImg)
    canvas.data.splashScreen = splashScreenImg
    displayScreenImg = Image.open('display-screen.png')
    displayScreenImg = ImageTk.PhotoImage(displayScreenImg)
    canvas.data.displayScreen = displayScreenImg
    options = Image.open('options-bar.png')
    options = ImageTk.PhotoImage(options)
    canvas.data.options = options
    heading = Image.open('headings-bar.png')
    heading = ImageTk.PhotoImage(heading)
    canvas.data.heading = heading

def init(canvas):
    canvas.data.screen1 = True
    canvas.data.screen2 = False
    canvas.data.proceed = False
    canvas.data.debug = False
    initializeButtons(canvas)
    canvas.data.originalImgFile = None #user chooses a file
    canvas.data.intermediateFile = 'intermediate-edge.png'
    canvas.data.edgeImageFile = 'edgeImage.png'
    canvas.data.filledImageFile = 'filledImage.png'
    canvas.data.keptEdgesFile = 'kept-edges.png'
    canvas.data.grayScaleFile = 'gray-img.png'
    canvas.data.scaledImgFile = 'scaled-img.png'
    initializeGraphics(canvas)
    redrawAll(canvas)

def run():
    # from class notes
    # create the root and the canvas
    root = Tk()
    root.resizable(width=FALSE, height=FALSE)
    (heading, options, margin, maxImageSize) = (50, 50, 50, 300)
    canvasWidth = (2*maxImageSize)+(4*margin)
    canvasHeight = maxImageSize+(2*margin)+heading+options
    canvas = Canvas(root, width = canvasWidth, height = canvasHeight)
    # Set up canvas data and call init
    class Struct(): pass
    canvas.data = Struct()
    canvas.data.canvasWidth = canvasWidth
    canvas.data.canvasHeight = canvasHeight
    canvas.data.optionsBar = options
    canvas.data.headingBar = heading
    init(canvas)
    timerFired(canvas)
    # and launch the app
    root.mainloop()
    # This call BLOCKS (so your program waits until you close the window!)

run()
