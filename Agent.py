# Your Agent for solving Raven's Progressive Matrices. You MUST modify this file.
#
# You may also create and submit new files in addition to modifying this file.
#
# Make sure your file retains methods with the signatures:
# def __init__(self)
# def Solve(self,problem)
#
# These methods will be necessary for the project's main method to run.

# Install Pillow and uncomment this line to access image processing.

from PIL import Image, ImageChops
from copy import deepcopy
from Utilities import Transformation , Attribute , Conversion
from TransformationFinder import TransformationFinder
import sys

class Agent:
    # The default constructor for your Agent. Make sure to execute any
    # processing necessary before your Agent starts solving problems here.
    #
    # Do not add any variables to this signature; they will not be used by
    # main().
    def __init__(self):
        sys.setrecursionlimit(10000)
        self.problem_number = 0
        self.TwoX2ChoiceCount = 6
        self.ThreeX3ChoiceCount = 8
        self.answerChoices = []

    # The primary method for solving incoming Raven's Progressive Matrices.
    # For each problem, your Agent's Solve() method will be called. At the
    # conclusion of Solve(), your Agent should return an integer representing its
    # answer to the question: "1", "2", "3", "4", "5", or "6". These integers
    # are also the Names of the individual RavensFigures, obtained through
    # RavensFigure.getName() (as Strings).
    #
    # In addition to returning your answer at the end of the method, your Agent
    # may also call problem.checkAnswer(int givenAnswer). The parameter
    # passed to checkAnswer should be your Agent's current guess for the
    # problem; checkAnswer will return the correct answer to the problem. This
    # allows your Agent to check its answer. Note, however, that after your
    # agent has called checkAnswer, it will *not* be able to change its answer.
    # checkAnswer is used to allow your Agent to learn from its incorrect
    # answers; however, your Agent cannot change the answer to a question it
    # has already answered.
    #
    # If your Agent calls checkAnswer during execution of Solve, the answer it
    # returns will be ignored; otherwise, the answer returned at the end of
    # Solve will be taken as your Agent's answer to this problem.
    #
    # Make sure to return your answer *as an integer* at the end of Solve().
    # Returning your answer as a string may cause your program to crash.
    def Solve(self,problem):
        self.problem_number += 1
        print("Solving "+str(self.problem_number))
        self.Initialize()

        if problem.problemType == '3x3':
            #Get images
            A = problem.figures['A'].visualFilename
            A = self.ToBinary(A)
            B = problem.figures['B'].visualFilename
            B = self.ToBinary(B)
            C = problem.figures['C'].visualFilename
            C = self.ToBinary(C)
            D = problem.figures['D'].visualFilename
            D = self.ToBinary(D)
            E = problem.figures['E'].visualFilename
            E = self.ToBinary(E)
            F = problem.figures['F'].visualFilename
            F = self.ToBinary(F)
            G = problem.figures['G'].visualFilename
            G = self.ToBinary(G)
            H = problem.figures['H'].visualFilename
            H = self.ToBinary(H)
            for i in range(1,self.ThreeX3ChoiceCount+1):
                self.answerChoices.append(problem.figures[str(i)].visualFilename)
            #Find Tx
            Tx_Hor = self.FindTransformation(A,B,C)
            self.dispTx(Tx_Hor)
            Tx_Ver = self.FindTransformation(A,D,G)
            self.dispTx(Tx_Ver)

            if self.problem_number == 3:
                #tx = TransformationFinder()
                #t2 = tx.RepetitionByTranslation(A,B)
                pass
        result = problem.correctAnswer
        """
        #2x2 solving (Assuming A,B,C and D only in rpm)
        A = problem.figures['A']
        B = problem.figures['B']
        C = problem.figures['C']
        for i in range(1,self.TwoX2ChoiceCount+1):
            self.answerChoices.append(problem.figures[str(i)])
        #Correspondence finding
        rowPairs = self.FindCorrespondingObjects(A,B)
        colPairs = self.FindCorrespondingObjects(A,C)
        #Horizontal Transformation List (Transformation to right - Tr)
        Tr = self.GetTransformationList(A,B,rowPairs)
        #Vertical Transformation List (Transformation to bottom - Tc)
        Tc = self.GetTransformationList(A,C,colPairs)
        #Generate and Test
        Dr = self.Generate(Tr,C,colPairs) #generated object for col wise transformation. colPairs are passed to know which object's transformation from A is to be applied to C
        Dc = self.Generate(Tc,B,rowPairs)
        D = self.Combine(Dr,Dc)
        result = self.Test(D)
        """
        print(" Answer: "+str(result))
        return result

    def Initialize(self):
        self.answerChoices = []

    def FindTransformation(self,A,B,C):
        TxManager = TransformationFinder()
        #Super Transformations (level 1)
        Tx0 = TxManager.FindSuperTx(A,B,C)
        #Transformations (level 2)
        Tx1 = TxManager.FindTx(A,B)
        Tx2 = TxManager.FindTx(B,C)
        Tx = [Tx0,Tx1,Tx2]
        return Tx

    def ToBinary(self,A):
        image_file = Image.open(A) # open colour image
        image_file = image_file.convert('1') # convert image to black and white
        image_file = ImageChops.invert(image_file)
        #new_name = "A.png"
        #image_file.save(new_name)
        return image_file

    def dispTx(self,txs):
        for tx in txs[:]:
            print("=>"+str(tx.txType))
            for k,v in tx.txScores.items():
                print(str(k)+":"+str(v))
            print(str(tx.txDetails))
            print(".")
        return
    """
    def GetTransformationList(self, A, B, pairs):
        tr = {}
        for k in sorted(A.objects.keys()):
            pair = pairs[k]
            if pair != "none":
                tr[k] = self.FindTransformation(A.objects[k],B.objects[pair])
            else:
                tr[k] = self.FindTransformation(A.objects[k])
        return tr

    def FindTransformation(self, a, b="none"):
        trans = []
        if b != "none":
            if Attribute.shape.name in a.attributes and Attribute.shape.name in b.attributes:
                if b.attributes[Attribute.shape.name] != a.attributes[Attribute.shape.name]:
                    conversion = Conversion(Transformation.ShapeChange,a.attributes[Attribute.shape.name],b.attributes[Attribute.shape.name])
                    trans.append(conversion)
            if Attribute.angle.name in a.attributes and Attribute.angle.name in b.attributes:
                if b.attributes[Attribute.angle.name] != a.attributes[Attribute.angle.name]:
                    bAngle = int(b.attributes[Attribute.angle.name])
                    aAngle = int(a.attributes[Attribute.angle.name])
                    if bAngle - aAngle == 90 or bAngle - aAngle == 270:
                        conversion = Conversion(Transformation.Reflect,a.attributes[Attribute.angle.name],b.attributes[Attribute.angle.name])
                    else:
                        conversion = Conversion(Transformation.Rotate,a.attributes[Attribute.angle.name],b.attributes[Attribute.angle.name])
                    trans.append(conversion)
            if Attribute.fill.name in a.attributes and Attribute.fill.name in b.attributes:
                if b.attributes[Attribute.fill.name] != a.attributes[Attribute.fill.name]:
                    conversion = Conversion(Transformation.Fill,a.attributes[Attribute.fill.name],b.attributes[Attribute.fill.name])
                    trans.append(conversion)
            if Attribute.size.name in a.attributes and Attribute.size.name in b.attributes:
                if b.attributes[Attribute.size.name] != a.attributes[Attribute.size.name]:
                    conversion = Conversion(Transformation.Scale,a.attributes[Attribute.size.name],b.attributes[Attribute.size.name])
                    trans.append(conversion)
            if Attribute.alignment.name in a.attributes and Attribute.alignment.name in b.attributes:
                if b.attributes[Attribute.alignment.name] != a.attributes[Attribute.alignment.name]:
                    conversion = Conversion(Transformation.Translate,a.attributes[Attribute.alignment.name],b.attributes[Attribute.alignment.name])
                    trans.append(conversion)
        else:
            conversion = Conversion(Transformation.Delete,"none","none")
            trans.append(conversion)
        if trans == []:
            conversion = Conversion(Transformation.NoChange,"none","none")
            trans.append(conversion)
        return trans

    def FindCorrespondingObjects(self, A, B):
        pairs = {}
        difference = {}
        toDecidePairs = {}
        availableA = list(A.objects.keys())
        availableB = list(B.objects.keys())
        for objAKey,objAValue in A.objects.items():
            difference[objAKey] = {}
            for objBKey,objBValue in B.objects.items():
                difference[objAKey][objBKey] = self.GetDifference(objAValue,objBValue)
        for k1,v1 in difference.items():
            max = 100
            foundk2 = ""
            foundv2 = ""
            for k2,v2 in v1.items():
                if v2 < max:
                    foundk2 = k2
                    foundv2 = v2
                    max = v2
            if foundv2 == 0:
                pairs[k1] = foundk2
                availableB.remove(foundk2)
                availableA.remove(k1)
            else:
                toDecidePairs[k1] = foundk2
        for k,v in toDecidePairs.items():
            if v in availableB:
                pairs[k] = v
                availableB.remove(v)
                availableA.remove(k)
            else:
                pairs[k] = "none"
        return pairs

    def GetDifference(self, aObj, bObj):
        diff = 0
        if Attribute.shape.name in aObj.attributes and Attribute.shape.name in bObj.attributes:
            if bObj.attributes[Attribute.shape.name] != aObj.attributes[Attribute.shape.name]:
                diff += Attribute.shape.value
        if Attribute.size.name in aObj.attributes and Attribute.size.name in bObj.attributes:
            if bObj.attributes[Attribute.size.name] != aObj.attributes[Attribute.size.name]:
                diff += Attribute.size.value
        if Attribute.fill.name in aObj.attributes and Attribute.fill.name in bObj.attributes:
            if bObj.attributes[Attribute.fill.name] != aObj.attributes[Attribute.fill.name]:
                diff += Attribute.fill.value
        if Attribute.angle.name in aObj.attributes and Attribute.angle.name in bObj.attributes:
            if bObj.attributes[Attribute.angle.name] != aObj.attributes[Attribute.angle.name]:
                diff += Attribute.angle.value
        if Attribute.alignment.name in aObj.attributes and Attribute.alignment.name in bObj.attributes:
            if bObj.attributes[Attribute.alignment.name] != aObj.attributes[Attribute.alignment.name]:
                diff += Attribute.alignment.value
        if Attribute.above.name in aObj.attributes and Attribute.above.name not in bObj.attributes:
            diff += Attribute.above.value
        elif Attribute.above.name not in aObj.attributes and Attribute.above.name in bObj.attributes:
            diff += Attribute.above.value
        #have ot add inside attribute if needed
        return diff

    def Generate(self,Trans, Fig, Pairs):
        finalFig = deepcopy(Fig)
        #this works for A to C since Pairs contains obj of A only. what to do if more pairs are added for 3x3?
        for k,v in Pairs.items():
            if v != "none":
                curObject = finalFig.objects[v]
                for item in Trans[k]:
                    if item.TransformationType == Transformation.Delete:
                        del finalFig.objects[v]
                        break
                    elif item.TransformationType != Transformation.NoChange:
                        if Attribute.shape.name in curObject.attributes:
                            if item.TransformationType == Transformation.ShapeChange:
                                curObject.attributes[Attribute.shape.name] = item.getConvertedValue()
                        if Attribute.angle.name in curObject.attributes:
                            if item.TransformationType == Transformation.Reflect:
                                curObject.attributes[Attribute.angle.name] = item.getConvertedValue(curObject.attributes[Attribute.angle.name])
                        if Attribute.size.name in curObject.attributes:
                            if item.TransformationType == Transformation.Scale:
                                curObject.attributes[Attribute.size.name] = item.getConvertedValue()
                        if Attribute.angle.name in curObject.attributes:
                            if item.TransformationType == Transformation.Rotate:
                                curObject.attributes[Attribute.angle.name] = item.getConvertedValue(curObject.attributes[Attribute.angle.name])
                        if Attribute.fill.name in curObject.attributes:
                            if item.TransformationType == Transformation.Fill:
                                curObject.attributes[Attribute.fill.name] = item.getConvertedValue()
                        if Attribute.alignment.name in curObject.attributes:
                            if item.TransformationType == Transformation.Translate:
                                curObject.attributes[Attribute.alignment.name] = item.getConvertedValue(curObject.attributes[Attribute.alignment.name])
        return finalFig

    def Test(self,Fig):
        matchPercentage = 0
        matchChoiceNumber = 1
        for choice in self.answerChoices:
            pairs,availableInFig,availableInChoice = self.FindMatchingObjects(Fig,choice)
            if len(availableInFig) == 0 and len(availableInChoice) == 0:
                return int(choice.name)
            else:
                percentage = (1/(len(availableInFig)+len(availableInChoice)+1))*100
                if percentage >= matchPercentage:
                    matchPercentage = percentage
                    matchChoiceNumber = int(choice.name)
        return matchChoiceNumber

    def IsEqualObjects(self,a,b):
        if Attribute.shape.name in a.attributes and Attribute.shape.name in b.attributes:
            if b.attributes[Attribute.shape.name] != a.attributes[Attribute.shape.name]:
                return False
        if Attribute.fill.name in a.attributes and Attribute.fill.name in b.attributes:
            if b.attributes[Attribute.fill.name] != a.attributes[Attribute.fill.name]:
                return False
        if Attribute.size.name in a.attributes and Attribute.size.name in b.attributes:
            if b.attributes[Attribute.size.name] != a.attributes[Attribute.size.name]:
                return False
        if Attribute.angle.name in a.attributes and Attribute.angle.name in b.attributes:
            if b.attributes[Attribute.angle.name] != a.attributes[Attribute.angle.name]:
                return False
        if Attribute.alignment.name in a.attributes and Attribute.alignment.name in b.attributes:
            if b.attributes[Attribute.alignment.name] != a.attributes[Attribute.alignment.name]:
                return False
        return True

    def Combine(self, fig1, fig2):
        pairs,availableInFig1,availableInFig2 = self.FindMatchingObjects(fig1, fig2)
        if len(availableInFig1) == 0 and len(availableInFig2) == 0:
            return fig1
        elif len(availableInFig1) > 0:
            fig = deepcopy(fig2)
            #add to fig2 and return
            for objName in availableInFig1:
                fig.objects[objName] = deepcopy(fig1.objects[objName])
            return fig
        elif len(availableInFig2) > 0:
            fig = deepcopy(fig1)
            #add to fig1 and return
            for objName in availableInFig2:
                fig.objects[objName] = deepcopy(fig2.objects[objName])
            return fig
        pass

    def FindMatchingObjects(self, A, B):
        pairs = {}
        difference = {}
        availableA = list(A.objects.keys())
        availableB = list(B.objects.keys())
        for objAKey,objAValue in A.objects.items():
            difference[objAKey] = {}
            for objBKey,objBValue in B.objects.items():
                difference[objAKey][objBKey] = self.GetDifference(objAValue,objBValue)
        for k1,v1 in difference.items():
            max = 100
            foundk2 = ""
            foundv2 = ""
            for k2,v2 in v1.items():
                if v2 < max:
                    foundk2 = k2
                    foundv2 = v2
                    max = v2
            if foundv2 == 0:
                pairs[k1] = foundk2
                availableB.remove(foundk2)
                availableA.remove(k1)
        return pairs,availableA,availableB

    def PrintValue(self,transList):
        for k,a in transList.items():
            print(" "+k+":")
            for b in a:
                print("  "+b.toString())

    def PrintPairs(self,pairs):
        for k,v in pairs.items():
            print(" "+k+":"+v+",")

    def PrintObject(self,fig):
        for k1 in sorted(fig.objects.keys()):
            print(" "+k1+":")
            for k,v in fig.objects[k1].attributes.items():
                print("  "+k+":"+v)
    """