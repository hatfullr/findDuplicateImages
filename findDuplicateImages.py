# Dependencies:
#     Python3
#     numpy
#     OpenCV
#     shutil
#
# How to use:
# 1.) Place this script in the directory containing all your photos OR
#     put the script anywhere and edit the line,
#          directory = ""
#     to look like,
#          directory = "path/to/your/directory"
# 2.) Create a directory there called "Duplicates"
# 3.) Run the script with "python findDuplicateImages.py"
# Output will be produced showing you exactly what the program is doing.
# None of your files will be lost or altered, they will only be moved to 
# the "Duplicates" directory. You can choose to delete this directory 
# after running the script.
#
# Written by Roger Hatfull (04/2020)

import numpy as np
import glob
import cv2 #OpenCV
import shutil
import os
from multiprocessing import Pool

# We will utilize multiprocessing where we can

# Convert each image to greyscale and same image sizes
def convert_images(imagenames,chunk,imagesizes=(10,10)):
    images = [None]*len(imagenames)
    imageres = [None]*len(imagenames)

    for i in range(0,len(imagenames)):
        #print( "%5.1f%% Reading %s" % (i/float(len(imagenames))*100., imagenames[i]) )
        # Convert all images to grayscale
        images[i] = cv2.cvtColor(cv2.imread(imagenames[i]),cv2.COLOR_BGR2GRAY)
        #resx, resy = images[i].shape
        #imageres[i] = resx * resy
        imageres[i] = os.path.getsize(imagenames[i])
        # Make all images the same size
        images[i] = cv2.resize(images[i], imagesizes)
    return images,imageres,chunk

def find_duplicates(image_idx,images,imagenames,imageres):
    # Find images in "images" that are duplicates of "image"
    # image_idx will always be fed into this function in a monotonic order
    duplicates = [k for k in range(image_idx,len(images)) if np.allclose(images[image_idx],images[k],rtol=2e-1)]
    return duplicates
    
if __name__ == '__main__':
    directory = ""
    dupdir = directory+"./Duplicates"
    types = ('*.png', '*.jpg', '*.jpeg')
    imagenames = []
    for files in types:
        imagenames.extend(glob.glob(directory+"\\"+files))
        
    pool = Pool()
    nprocs = pool._processes
    
    chunks = np.array_split(np.arange(len(imagenames),dtype=int),nprocs)
    for i in range(0,len(chunks)):
        chunks[i] = chunks[i].tolist()

    print("Converting all images to greyscale and same resolution")
    print("Using",nprocs,"processes")
    
    p = [None]*nprocs
    for i in range(0,nprocs):
        p[i] = pool.apply_async(convert_images,args=([imagenames[k] for k in chunks[i]],chunks[i]))

    images = [None]*len(imagenames)
    imageres = [None]*len(imagenames)
    for i in range(0,nprocs):
        imgs, imgres, chunk = p[i].get()
        for j,k in zip(range(0,len(imgs)),chunk):
            images[k] = imgs[j]
            imageres[k] = imgres[j]
    
    print("Checking for duplicates")

    pool.close()

    imglist = [None]*len(images)
    for i in range(0,len(images)):
        imglist[i] = find_duplicates(i,images,imagenames,imageres)

    fmt = "%"+str(int(np.log10(len(images)))+1)+"i %"+str(int(np.log10(max(imageres)))+1)+"i %s"

    duplicates = []
    for i in range(0,len(imglist)):
        if len(imglist[i]) > 1:
            print("Duplicates detected:")
            for j in range(0,len(imglist[i])):
                print(fmt % (imglist[i][j],imageres[imglist[i][j]],imagenames[imglist[i][j]]))
            # Find the image with the largest resolution
            imglist_res = [imageres[j] for j in imglist[i]]
            maxres = max(imglist_res)
            maxres_idx = imglist[i][imglist_res.index(maxres)]
            # Now find all the images that have worse or same resolution
            for j in imglist[i]:
                if j not in duplicates:
                    #print(i,imagenames[i])
                    #print(j,imagenames[j])
                    #if maxres == imageres[j]:
                    #    print("Same file size on",maxres_idx,"and",j)
                    if imageres[j] <= maxres:
                        if imagenames[j] != imagenames[maxres_idx]:
                            print("Will remove",j,imagenames[j])
                            duplicates.append(j)
            print("Duplicates array =",duplicates)
            print("")

    print("Moved to",dupdir,":")
    for i in range(0,len(duplicates)):
        shutil.move(imagenames[duplicates[i]], dupdir+"\\"+imagenames[duplicates[i]].split("\\")[-1])
        print(fmt % (duplicates[i],imageres[duplicates[i]],imagenames[duplicates[i]]))

