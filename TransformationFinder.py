__author__ = 'Bhuvanesh'

from Utilities import Transformation, Blob, BlobPairInfo
from PIL import Image, ImageChops, ImageDraw
from collections import deque, defaultdict
import math
import time

class TransformationFinder:
    def __init__(self):
        self.PIXEL_PRESENT = 1
        self.PIXEL_NOT_PRESENT = 0
        self.IMAGE_WIDTH = 0
        self.IMAGE_HEIGHT = 0
        self.ThresholdScore = 99

    def FindTx(self,A,B,C):
        self.IMAGE_WIDTH = A.width
        self.IMAGE_HEIGHT = A.height
        Tx = []
        self.BlobsA = self.GetBlobs(A)
        #self.showBlobs(A,BlobsA)
        self.BlobsB = self.GetBlobs(B)
        self.BlobsC = self.GetBlobs(C)

        #Super Transformations (level 1)
        Tx0 = self.FindSuperTx(A,B,C)
        Tx.append(Tx0)

        #Figure Transformations (level 2)
        Tx1 = self.FindFigureTx(A,B)
        Tx2 = self.FindFigureTx(B,C)
        Tx.append([Tx1,Tx2])

        #Blob Transformations (level 3)
        if max(Tx1.getHighestScore(),Tx2.getHighestScore()) < self.ThresholdScore:
            Tx3 = self.FindBlobTx(A,self.BlobsA,B,self.BlobsB)
            Tx4 = self.FindBlobTx(B,self.BlobsB,C,self.BlobsC)
            Tx5 = self.FindBlobTx(A,self.BlobsA,C,self.BlobsC)
            #                   0                           4                   6                   7
            #details contains (same,morph,translate,scale,addition,deletion,blobCountDiffernce,morph pattern)
            if len(Tx3.getBestTxDetails())>0 and len(Tx4.getBestTxDetails())>0:
                if Tx3.getBestTxDetails()[6] != Tx4.getBestTxDetails()[6]:
                    Tx4.setBestTxDetails(Tx4.getBestTxDetails()[0:6]+(99,))#99denote no common increasing or decreasing blob count difference
            if len(Tx5.getBestTxDetails())>0 and Tx5.getBestTxDetails()[1] >=1:
                Tx3.setBestTxDetails(Tx3.getBestTxDetails()+(1,)) #Adding morph pattern bit
                Tx4.setBestTxDetails(Tx4.getBestTxDetails()+(1,))
            else:
                Tx3.setBestTxDetails(Tx3.getBestTxDetails()+(0,)) #Adding morph pattern bit
                Tx4.setBestTxDetails(Tx4.getBestTxDetails()+(0,))
            Tx.append([Tx3,Tx4])
        return Tx

    def FindDiagTx(self,A,B):
        self.IMAGE_WIDTH = A.width
        self.IMAGE_HEIGHT = A.height
        Tx = []
        self.BlobsA = self.GetBlobs(A)
        self.BlobsB = self.GetBlobs(B)

        #Figure Transformations (level 2)
        Tx1 = self.FindFigureTx(A,B)
        Tx.append(Tx1)

        #Blob Transformations (level 3)
        if Tx1.getHighestScore() < self.ThresholdScore:
            Tx3 = self.FindBlobTx(A,self.BlobsA,B,self.BlobsB)
            #details contains (same,morph,translate,scale,addition,deletion,morph pattern)
            if len(Tx3.getBestTxDetails())>0 and Tx3.getBestTxDetails()[1] >=1:
                Tx3.setBestTxDetails(Tx3.getBestTxDetails()+(1,)) #Adding morph pattern bit
            else:
                Tx3.setBestTxDetails(Tx3.getBestTxDetails()+(0,)) #Adding morph pattern bit
            Tx.append(Tx3)
        return Tx

    def FindSuperTx(self,A,B,C):
        Tx = TransformationFrame()
        Tx.assignTxScore(Transformation.ConstantAddition,self.ConstantAddition(A,B,C))
        Tx.assignTxScore(Transformation.ConstantSubtraction,self.ConstantSubtraction(A,B,C))
        Tx.assignTxScore(Transformation.Addition,self.Addition(A,B,C))
        Tx.assignTxScore(Transformation.Subtraction,self.Subtraction(A,B,C))
        Tx.assignTxScore(Transformation.AddcumSub,self.AddcumSub(A,B,C))
        Tx.assignTxScore(Transformation.Common,self.Common(A,B,C))
        Tx.assignTxScore(Transformation.Divergence,self.Divergence(A,B,C))
        Tx.assignTxScore(Transformation.Convergence,self.Convergence(A,B,C))
        correspAC, additionCnt, deletionCnt = self.GetBlobCorrespondence(self.BlobsA,self.BlobsC)
        ACMetaData = self.GetBlobMetaData(correspAC,self.BlobsA,self.BlobsC)
        if ACMetaData['repetition'] == False and ACMetaData['oneToOne'] == True:
            Tx.assignTxScore(Transformation.Migration,self.Migration(A,B,C))
        return Tx

    def FindFigureTx(self,A,B):
        Tx = TransformationFrame()
        #Transformations (level 2)
        Tx.assignTxScore(Transformation.Same,(self.Same(A,B),0))
        if Tx.getHighestScore() < self.ThresholdScore:
            Tx.assignTxScore(Transformation.RepetitionByExpansion,self.RepetitionByExpansion(A,B))
            Tx.assignTxScore(Transformation.RepetitionByTranslation,self.RepetitionByTranslation(A,B))
        #Tx.assignTxScore(Transformation.RepetitionByCircularTranslation,self.RepetitionByCircularTranslation(A,B))
        return Tx

    def FindBlobTx(self,A,BlobsA,B,BlobsB):
        Tx = TransformationFrame()
        Tx.Blobs.append(BlobsA)
        Tx.Blobs.append(BlobsB)
        Tx.corresp, additionsToBlobsB, deletionsInBlobsA = self.GetBlobCorrespondence(BlobsA, BlobsB)
        Tx.BlobMetaData = self.GetBlobMetaData(Tx.corresp,BlobsA,BlobsB)
        numberMorphed = 0
        #if  additionsToBlobsB==deletionsInBlobsA:
        #    numberMorphed = additionsToBlobsB
        #    additionsToBlobsB = 0
        #    deletionsInBlobsA = 0
        Tx.BlobMetaData['AdditionCount'] = additionsToBlobsB
        Tx.BlobMetaData['DeletionCount'] = deletionsInBlobsA
        #Blob Transformations ( level 3)
        if Tx.BlobMetaData['repetition'] == False:
            #only if more than one obj is present in figure
            if len(Tx.corresp.keys()) >= 1:
                details = self.BlobTransforms(Tx.corresp,Tx.Blobs[0],Tx.Blobs[1])
                details = (details[0],details[1],details[2]+numberMorphed,details[3],details[4])
                details = details + (Tx.BlobMetaData['AdditionCount'],Tx.BlobMetaData['DeletionCount'],Tx.BlobMetaData['blobCountDifference'])
                Tx.assignTxScore(Transformation.BlobTransforms,details)
                Tx.assignTxScore(Transformation.ScalingOfOneObject,self.ScalingOfOneObject(Tx.corresp,Tx.Blobs[0],Tx.Blobs[1]))
                Tx.assignTxScore(Transformation.TranslationOfOneObject,self.TranslationOfOneObject(Tx.corresp,Tx.Blobs[0],Tx.Blobs[1]))
        return Tx

    def BlobTransforms(self, corresp, BlobsA, BlobsB):
        morphCount = 0
        translationCount = 0
        scalingCount = 0
        sameCount = 0
        for aid,bIdAndVals in corresp.items():
            pairInfo = bIdAndVals[0][2]
            if pairInfo.isMorph():
                morphCount += 1
            if pairInfo.isTranslated():
                translationCount += 1
            if pairInfo.isScaled():
                scalingCount += 1
            if pairInfo.isSame():
                sameCount += 1
        score = 99
        return score, sameCount, morphCount, translationCount, scalingCount

    def Addition(self,A,B,C):
        AplusB = ImageChops.lighter(A,B)
        score = self.Same(AplusB,C)
        return score, 0

    def Subtraction(self,A,B,C):
        AuB = ImageChops.lighter(A,B)
        Diff = ImageChops.difference(AuB,B)
        score = self.Same(Diff,C)
        return score, 0

    def AddcumSub(self,A,B,C):
        add = ImageChops.lighter(A,B)
        comm = ImageChops.darker(A,B)
        Diff = ImageChops.difference(add,comm)
        score = self.Same(Diff,C)
        return score, 0

    def Common(self,A,B,C):
        common = ImageChops.darker(A,B)
        score = self.Same(common,C)
        return score, 0

    def Migration(self,A,B,C):
        #Horizontal migration
        #A super transformation where blobs in A from their end migrate to pos in C in the other end via B
        if self.IMAGE_WIDTH == 0 or self.IMAGE_HEIGHT == 0:
            self.IMAGE_WIDTH = A.width
            self.IMAGE_HEIGHT = A.height
        migDir = []
        migCol = []
        ABscore = 0
        BCscore = 0
        croppedBlobs = []
        migImage = Image.new("1",(self.IMAGE_WIDTH,self.IMAGE_HEIGHT))
        if len(self.BlobsA) >0:
            for b in self.BlobsA[:]:
                if b.startCol<self.IMAGE_WIDTH/2:
                    migDir.append(1)
                else:
                    migDir.append(-1)
                migCol.append(b.startCol)
                cropped = A.crop((b.startCol,b.startRow,b.endCol,b.endRow))
                croppedBlobs.append(cropped)
            for i in range(1,int(self.IMAGE_WIDTH  - migCol[0])+1):
                migImage = Image.new("1",(self.IMAGE_WIDTH,self.IMAGE_HEIGHT))
                for b in self.BlobsA:
                    newImage = Image.new("1",(self.IMAGE_WIDTH,self.IMAGE_HEIGHT))
                    migCol[b.id] = migCol[b.id]+migDir[b.id]
                    newImage.paste(croppedBlobs[b.id],(migCol[b.id],b.startRow))
                    migImage = ImageChops.lighter(migImage,newImage)
                score = self.Similarity(migImage,B)
                if score >= 98:
                    ABscore = score
                    break
            #migImage.save(str(time.time())+"_AB.png","PNG")
            if ABscore >= 98:
                for i in range(1,int(self.IMAGE_WIDTH - migCol[0])+1):
                    migImage = Image.new("1",(self.IMAGE_WIDTH,self.IMAGE_HEIGHT))
                    for b in self.BlobsA:
                        newImage = Image.new("1",(self.IMAGE_WIDTH,self.IMAGE_HEIGHT))
                        migCol[b.id] = migCol[b.id]+migDir[b.id]
                        newImage.paste(croppedBlobs[b.id],(migCol[b.id],b.startRow))
                        migImage = ImageChops.lighter(migImage,newImage)
                    score = self.Similarity(migImage,C)
                    if score >= 96:
                        BCscore = score
                        break
            #migImage.save(str(time.time())+"_BC.png","PNG")
            if ABscore>=98 and BCscore >= 96:
                return (ABscore+BCscore)/2, ABscore, BCscore
            else:
                #vertical migration
                migDir = []
                #migCol is migRow here
                migCol = []
                ABscore = 0
                BCscore = 0
                croppedBlobs = []
                migImage = Image.new("1",(self.IMAGE_WIDTH,self.IMAGE_HEIGHT))
                for b in self.BlobsA[:]:
                    if b.startRow<self.IMAGE_HEIGHT/2:
                        migDir.append(1)
                    else:
                        migDir.append(-1)
                    migCol.append(b.startRow)
                    cropped = A.crop((b.startCol,b.startRow,b.endCol,b.endRow))
                    croppedBlobs.append(cropped)
                for i in range(1,int(self.IMAGE_HEIGHT - migCol[0])+1):
                    migImage = Image.new("1",(self.IMAGE_WIDTH,self.IMAGE_HEIGHT))
                    for b in self.BlobsA:
                        newImage = Image.new("1",(self.IMAGE_WIDTH,self.IMAGE_HEIGHT))
                        migCol[b.id] = migCol[b.id]+migDir[b.id]
                        newImage.paste(croppedBlobs[b.id],(b.startCol,migCol[b.id]))
                        migImage = ImageChops.lighter(migImage,newImage)
                    score = self.Similarity(migImage,B)
                    if score >= 98:
                        ABscore = score
                        break
                #migImage.save(str(time.time())+"_AB.png","PNG")
                if ABscore >= 98:
                    for i in range(1,int(self.IMAGE_HEIGHT - migCol[0])+1):
                        migImage = Image.new("1",(self.IMAGE_WIDTH,self.IMAGE_HEIGHT))
                        for b in self.BlobsA:
                            newImage = Image.new("1",(self.IMAGE_WIDTH,self.IMAGE_HEIGHT))
                            migCol[b.id] = migCol[b.id]+migDir[b.id]
                            newImage.paste(croppedBlobs[b.id],(b.startCol,migCol[b.id]))
                            migImage = ImageChops.lighter(migImage,newImage)
                        score = self.Similarity(migImage,C)
                        if score >= 96:
                            BCscore = score
                            break
        #migImage.save(str(time.time())+"_BC.png","PNG")
        return (ABscore+BCscore)/2, ABscore, BCscore

    def Divergence(self,A,B,C):
        #A super transformation where object in A splits into two
        ABscore, ABloc, ABlor, ABroc, ABror = self.RepetitionByTranslation(A,B)
        ACscore, ACloc, AClor, ACroc, ACror = self.RepetitionByTranslation(A,C)
        if abs(ABscore-ACscore)<3:
            return (ABscore+ACscore)/2, ABscore, ACscore
        return 0,0,0

    def Convergence(self,A,B,C):
        #A super transformation where objects in A merge into one
        return self.Divergence(C,B,A)

    def ConstantAddition(self,A,B,C):
        if self.Similarity(ImageChops.lighter(A,B),B)>99:
            AminusB = ImageChops.difference(A,B)
            ABAdditionArea = self.getFillPercentage(AminusB,0,0,AminusB.width,AminusB.height)
            if self.Similarity(ImageChops.lighter(B,C),C)>99:
                BminusC = ImageChops.difference(B,C)
                BCAdditionArea = self.getFillPercentage(BminusC,0,0,BminusC.width,BminusC.height)
                score = 0
                #print("In Const Add:")
                #print("AB Added area:"+str(ABAdditionArea))
                #print("BC Added area:"+str(BCAdditionArea))
                if ABAdditionArea > 1 and BCAdditionArea > 1:
                    if abs(ABAdditionArea - BCAdditionArea) < 4:
                        similarity = self.Similarity(C,ImageChops.lighter(B,ImageChops.difference(B,C)))
                        score = similarity
                return  score, ABAdditionArea, BCAdditionArea
        return 0,0,0

    def ConstantSubtraction(self,A,B,C):
        score, BCSubArea, ABSubArea = self.ConstantAddition(C,B,A)
        """
        AminusB = ImageChops.difference(A,B)
        ABSubArea = self.getFillPercentage(AminusB,0,0,AminusB.width,AminusB.height)
        BminusC = ImageChops.difference(B,C)
        BCSubArea = self.getFillPercentage(BminusC,0,0,BminusC.width,BminusC.height)
        score = 0
        #print("In Const Sub:")
        #print("AB Sub area:"+str(ABSubArea))
        #print("BC Sub area:"+str(BCSubArea))
        if ABSubArea > 1 and BCSubArea > 1:
            if abs(ABSubArea - BCSubArea) < 4:
                similarity = self.Similarity(B,ImageChops.lighter(C,ImageChops.difference(B,C)))
                score = similarity
        """
        return  score, ABSubArea, BCSubArea

    def ScalingOfOneObject(self,corresp, BlobsA, BlobsB):
        widthScaling = 0
        heightScaling = 0
        score = 0
        for k,v in corresp.items():
            #if all parameters are different 1 possibility is scaling
            if v[0][1] >= 3:
                if BlobsA[k].width!=BlobsB[v[0][0]] or BlobsA[k].height!=BlobsB[v[0][0]]:
                    widthScaling = BlobsB[v[0][0]].width/BlobsA[k].width
                    heightScaling = BlobsB[v[0][0]].height/BlobsA[k].height
                    score = 99
        return score, widthScaling, heightScaling

    def TranslationOfOneObject(self,corresp, BlobsA, BlobsB):
        data = []
        score = 0
        for k,v in corresp.items():
            colOffset, rowOffset = self.GetBlobOffset(BlobsA[k],BlobsB[v[0][0]])
            if colOffset<-1 or colOffset>1 or rowOffset<-1 or rowOffset>1:
                data.append((k,v[0][0],colOffset,rowOffset))
        if len(data)>0:
            score = 99
        return score,data

    def GetBlobOffset(self,a,b):
        colOffset = b.startCol - a.startCol
        rowOffset = b.startRow - a.startRow
        return colOffset, rowOffset

    def GetBlobMetaData(self, correspondences, ba, bb):
        repetition = False
        oneToOne = True
        fillPercentage = []
        for key,val in correspondences.items():
            if len(val)>1:
                repetition = True
                oneToOne = False
            else:
                fillPercentage.append((key,val,abs(ba[key].fill-bb[val[0][0]].fill)))
            if len(val) == 0:
                oneToOne = False
        if len(correspondences) < len(ba):
            oneToOne = False
        blobCountDifference = len(bb)-len(ba)
        metaData= {'repetition':repetition,'fillComparison':fillPercentage,'oneToOne':oneToOne,'blobCountDifference':blobCountDifference}
        return metaData
    """
    def RepetitionByCircularTranslation(self,A,B):
        #get trans details
        score = 0
        angle = 0
        aid = 0
        bid = 0
        for Aid, vals in corresp.items():
            if len(vals)>1:
                for t in vals[:]:
                    #for circular the start row and start col should be diff => the minDiff would be atlest 2
                    if t[1] >= 2:
                        Bid = t[0]
                s,ang = self.checkCircularTranslation(BlobsA[Aid], BlobsB[Bid])
                if s>score:
                    score = s
                    angle = ang
                    aid = Aid
                    bid = Bid
        #give them as blob frames
        details = score, angle, aid, bid, BlobsA, BlobsB
        return details
    """
    def checkCircularTranslation(self, blobA, blobB):
        centerRow = self.IMAGE_HEIGHT/2
        centerCol = self.IMAGE_WIDTH/2
        aCenter = ((blobA.startCol+blobA.endCol)/2,(blobA.startRow+blobA.endRow)/2)
        bCenter = ((blobB.startCol+blobB.endCol)/2,(blobB.startRow+blobB.endRow)/2)
        #aCenter = (blobA.startCol,blobA.startRow)
        #bCenter = (blobB.startCol,blobB.startRow)

        vecA = ((aCenter[0] - centerCol),(aCenter[1] - centerRow))
        vecB = ((bCenter[0] - centerCol),(bCenter[1] - centerRow))

        #normalized vectors
        distA = math.sqrt(vecA[0]*vecA[0]+vecA[1]*vecA[1])
        nVecA = (0,0)
        if distA != 0:
            nVecA = (vecA[0]/distA, vecA[1]/distA)

        distB = math.sqrt(vecB[0]*vecB[0]+vecB[1]*vecB[1])
        nVecB = (0,0)
        if distB != 0:
            nVecB = (vecB[0]/distB, vecB[1]/distB)
        if nVecA == (0,0) or nVecB == (0,0):
            return 0,0
        else:
            AdotB = nVecA[0]*nVecB[0] + nVecA[1]*nVecB[1]
            #print("AdotB"+str(AdotB))
            AdotB = max(-1,min(AdotB,1))
            angle = math.acos(AdotB)
            newVecA = (vecA[0]*math.cos(angle) - vecA[1]*math.sin(angle), vecA[0]*math.sin(angle) + vecA[1]*math.cos(angle))
            newBpos = (newVecA[0]+centerCol, newVecA[1]+centerRow)
            if newBpos[0] >= bCenter[0]-5 and newBpos[0] <= bCenter[0] + 5:
                if newBpos[1] >= bCenter[1]-5 and newBpos[1] <= bCenter[1] + 5:
                    return 100, angle
        return 0,0

    def GetBlobCorrespondence(self,BlobsA, BlobsB):
        MAX_DIFF = 6
        ba = BlobsA
        bb = BlobsB
        remainingABlobs = len(ba)
        remainingBBlobs = len(bb)
        notAssignedBBlobs = 0
        notAssignedABlobs = 0
        corresp = defaultdict(list)
        for b in bb[:]:
            assigned = False;
            minDiff = 99 #sum of attribute differences. attributes include start row, start col, width, height, fill
            corBlobId = 0
            blobPairInfo = BlobPairInfo()
            for a in ba[:]:
                s,info = self.getBlobSimilarityScoreAndInfo(b,a)
                if s<=minDiff:
                    if s<MAX_DIFF or info.iCenter:
                        minDiff = s
                        corBlobId = a.id
                        blobPairInfo = info
                        assigned = True
            if assigned:
                corresp[corBlobId].append((b.id,minDiff,blobPairInfo))
            else:
                notAssignedBBlobs += 1
        if len(corresp) < len(ba):
            notAssignedABlobs = len(ba) - len(corresp)
        AdditionCount = notAssignedBBlobs
        DeletionCount = notAssignedABlobs
        return corresp, AdditionCount, DeletionCount

    def getBlobSimilarityScoreAndInfo(self,b,a):
        score = 0
        info = BlobPairInfo()
        '''if b.startCol < a.startCol-1 or b.startCol > a.startCol+1:
            score = score + 1
        if b.startRow < a.startRow-1 or b.startRow > a.startRow+1:
            score = score + 1
        if b.width < a.width -1 or b.width > a.width +1:
            score = score + 1
        if b.height < a.height -1 or b.height > a.height +1:
            score = score + 1
        #if b.fill < a.fill-2 or b.fill > a.fill+2:
        #    score = score + 1
        '''
        if self.isInRange(b.startCol,a.startCol,1):
            info.iStartCol = True
        else:
            score += 1
        if self.isInRange(b.startRow,a.startRow,1):
            info.iStartRow = True
        else:
            score += 1
        if self.isInRange(b.width,a.width,1):
            info.iWidth = True
        else:
            score += 1
        if self.isInRange(b.height,a.height,1):
            info.iHeight = True
        else:
            score += 1
        if self.isInRange(b.fill,a.fill,0.011):#0.004
            info.iFill = True
        else:
            score += 1
        if self.isInRange(b.filledPixels, a.filledPixels,42):#change can be .5 percentage #42#34#22
            #if not self.isInRange(b.filledPixels,a.filledPixels,a.width*a.height*0.005):
            #   print("b fp: "+str(b.filledPixels)+" a fp:"+str(a.filledPixels)+" cond:"+str(a.width*a.height*0.005))
            #   print("a wh"+str(a.width)+","+str(a.height))
            info.iFilledPixels = True
        else:
            score += 1
        if self.isInRange(b.startCol+b.width/2,a.startCol+a.width/2, 5):
            if self.isInRange(b.startRow+b.height/2,a.startRow+a.height/2, 5):
                info.iCenter = True
        return score, info

    def isInRange(self,p,q,range):
        if p <= q+range and p >= q-range:
            return True
        else:
            return False

    def showBlobs(self,A,BlobsA):
        ad = ImageDraw.Draw(A,"1")
        for ba in BlobsA[:]:
            ad.rectangle([ba.startCol,ba.startRow,ba.endCol,ba.endRow], None, "blue")
        del ad
        A.show()

    def GetBlobs(self,A):
        imgD = A.copy()
        img1 = imgD.getdata()
        img = list(imgD.getdata())
        #delete weak links in image
        #end points or exceptioncal case handling - border case do
        for i in range(len(img)):
            if img[i]!=0:
                if img[i-1]==0 and img[i+1]==0:
                    img[i]=0
                if img[i - A.width]==0 and img[i + A.width]==0:
                    img[i]=0
        img1.putdata(img)
        Blobs = []
        id = 0
        bbox = img1.getbbox()
        while bbox!=None :
            #print(bbox)
            r = bbox[1]
            c = bbox[0]
            while c <= bbox[2]:
                if img[c + r*A.width] != 0:
                    break;
                c = c+1;
            img[c + r*A.width] = 0
            b = Blob()
            b.id = id
            #print("into fillBlob"+str(A.width))
            sr, sc, er, ec, img, filledPixels = self.fillBlob(img,A.width,c,r)
            #print("out of fillBlob"+str(er)+","+str(ec))
            b.startRow = sr
            b.startCol = sc
            b.endRow = er
            b.endCol = ec
            b.width = b.endCol - b.startCol + 1
            b.height = b.endRow - b.startRow + 1
            b.filledPixels = filledPixels
            b.fill = filledPixels/(b.width*b.height)#self.getFillPercentage(A,b.startCol,b.startRow,b.endCol,b.endRow)
            Blobs.append(b)
            id = id + 1
            img1.putdata(img)
            bbox = img1.getbbox()
        return Blobs

    def getFillPercentage(self,img,sc,sr,ec,er):
        pixels = img.crop((sc,sr,ec,er)).getdata()
        whitePixelCount = 0
        for pixel in pixels:
            if pixel != self.PIXEL_NOT_PRESENT:
                whitePixelCount += 1
        totalPixels = len(pixels)
        score = 100*(whitePixelCount/float(totalPixels))
        return score

    def fillBlob(self,img,width,c,r):
        sr = r
        sc = c
        er = r
        ec = c
        filledPixels = 0
        queue = deque()
        queue.append((c,r))
        while queue:
            c,r = queue.popleft()
            for i in range(-1,2):
                for j in range(-1,2):
                    if img[c+j + (r+i)*width] != 0:
                        img[c+j + (r+i)*width] = 0
                        filledPixels += 1
                        queue.append((c+j,r+i))
                        if r+i > er:
                            er = r+i
                        if c+j > ec:
                            ec = c+j
                        if r+i < sr:
                            sr = r+i
                        if c+j < sc:
                            sc = c+j
        return sr,sc, er, ec, img, filledPixels

    def RepetitionByTranslation(self,A,B):
        #a = A.copy()
        #b = B.copy()
        s = A.getbbox()
        f = B.getbbox()
        """
        sd = ImageDraw.Draw(a,"1")
        sd.rectangle([s[0]-5,s[1]-5,s[2]+5,s[3]+5], None, "blue")
        del sd
        a.show()
        fd = ImageDraw.Draw(b,"1")
        fd.rectangle([f[0]-5,f[1]-5,f[2]+5,f[3]+5], None, "blue")
        del fd
        b.show()
        """
        if f!=None and s!=None:
            left_offset_col = f[0] - s[0]
            #Get first active pixel from left
            sLRow = self.getFirstActiveRowInCol(A, s[1], s[3], s[0])
            fLRow = self.getFirstActiveRowInCol(B, f[1], f[3], f[0])
            #left_offset_row = f[1] - s[1]
            left_offset_row = fLRow - sLRow
            if abs(left_offset_col) > 5 or abs(left_offset_row) > 5:
                A1 = ImageChops.offset(A,left_offset_col,left_offset_row)

                right_offset_col = f[2] - s[2]
                #Get first active pixel from right
                sRRow = self.getLastActiveRowInCol(A, s[1], s[3], s[2]-1)
                fRRow = self.getLastActiveRowInCol(B, f[1], f[3], f[2]-1)
                right_offset_row = fRRow - sRRow
                #right_offset_row = f[3] - s[3]
                A2 = ImageChops.offset(A,right_offset_col,right_offset_row)
                ADash = ImageChops.lighter(A1, A2)
                #ADash.save("adash.png","PNG")
                #B.save("b.png","PNG")
                score = self.Similarity(ADash,B)
                details = score, left_offset_col, left_offset_row, right_offset_col, right_offset_row
                return details
            else:
                details = 0,0,0,0,0
                return details
        else:
            details = 0,0,0,0,0
            return details

    def getFirstActiveRowInCol(self,image, startRow, endRow, col):
        img = list(image.getdata())
        aRow = startRow
        for i in range(startRow,endRow+1):
            if img[col+i*image.width] != 0:
                aRow = i
                break
        return aRow

    def getLastActiveRowInCol(self,image, startRow, endRow, col):
        img = list(image.getdata())
        aRow = endRow
        for i in reversed(range(startRow,endRow+1)):
            if img[col+i*image.width] != 0:
                aRow = i
                break
        return aRow

    def RepetitionByExpansion(self,A,B):
        compA = A.getbbox()
        compB = B.getbbox()
        score = 0
        xGrowth = 0
        yGrowth = 0
        if compA!= None and compB!= None:
            if compB[0]<compA[0] and compB[2]>compA[2]:
                xGrowth = (compA[0] - compB[0] + compB[2] - compA[2])/2;
                if compB[1]<compA[1] and compB[3]>compA[3]:
                    yGrowth = (compA[1] - compB[1] + compB[3] - compA[3])/2
                    score = 97 #expansion
        details = score, xGrowth, yGrowth
        return details

    def Same(self,A,B):
        #returns the percentage of similarity
        highestScore = 0
        for i in range(-6,7,2):
            for j in range(-6,7,2):
                B1 = ImageChops.offset(B,i,j)
                s = self.Similarity(A,B1)
                if s>highestScore:
                    highestScore = s
        return highestScore

    def Similarity(self,A,B):
        diff = ImageChops.difference(A,B)
        pixels = diff.getdata()
        whitePixelCount = 0
        for pixel in pixels:
            if pixel != self.PIXEL_NOT_PRESENT:
                whitePixelCount += 1
        totalPixels = len(pixels)
        score = 100 - 100*(whitePixelCount/float(totalPixels))
        return score

class TransformationFrame:
    def __init__(self):
        self.txType = Transformation.Empty
        self.txScores = {Transformation.Empty:0}
        self.txDetails = ()
        self.Blobs= []
        self.BlobCorresp = {}
        self.BlobMetaData = {}
        self.blobFrames = []
    def assignTxScore(self,transType, details):
        self.txScores[transType] = details[0]
        if self.txScores[self.txType] < details[0]:
            self.txType = transType
            self.txDetails = details[1:]
    def getHighestScore(self):
        return self.txScores[self.txType]
    def getBestTransformation(self):
        return self.txType
    def getBestTxDetails(self):
        return self.txDetails
    def setBestTxDetails(self,details):
        self.txDetails = details

class BlobFrame:
    def __init__(self):
        self.type = Transformation.Empty
        self.src = 0
        self.dstn = 0
