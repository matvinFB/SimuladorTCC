from genericpath import exists
import numpy as np
import random
import itertools
import matplotlib.pyplot as plt
from numpy.core.fromnumeric import sort
import os

#Sensor class, not completed used in its full potential yet
class sensor:
    newid = itertools.count().__next__
    
    def __init__(self, pos, axis, precision, activeTime):
        self.pos = pos
        self.active = False
        self.axis = axis
        self.precision = precision
        self.activeTime = activeTime
        self.id = sensor.newid()
        self.activeTimeLeft = 0
    
    def __str__(self):
        return "Pos: {} \nActive: {} \nAxis: {}\nPrecision: {}\nActive Time: {}\nId:{}\n".format(self.pos, self.active, self.axis, self.precision, self.activeTime, self.id)
    
    def activation(self):
        #Lembrar de no futuro verificar se o sensor pode se reativar enquanto ainda está ativo

        rand = random.random()
        self.active = (rand<self.precision)
        
        if not self.active:
            print("Falha! ", self.id)
        
        self.activeTimeLeft = self.activeTime
    
    def decreaseTimeLeft(self):
        self.activeTimeLeft += (-1 if self.activeTimeLeft>0 else 0)
        self.active = (False if self.activeTimeLeft == 0 else True)
    
    def getId(self):
        return self.id
    
    def getActive(self):
        return self.active

#Sala means room in portuguese, I think the rest is pretty self explanatory  
class sala:
    def __init__(self, size, dist):
        self.size = tuple(map( lambda x: int(x/dist), size) )
        self.monitorMatrix = np.zeros(self.size)
        self.sensorMatrix = np.zeros(tuple(map( lambda x, y: x+y, self.size, (1,1) )))
        self.initialize()
    
    def initialize(self):
        x, y = self.size
        self.sensors = []
        acu = 1
        for i in range(x):
            pos = (i, 0)
            self.sensors.append(sensor( pos, 1, acu, 1))
            
        for i in range(y):
            pos = (0,i)
            self.sensors.append(sensor( pos, 0, acu, 1))

        for s in self.sensors:
            x, y = s.pos
            x += (1 if( s.axis ==1 )else 0)
            y +=(1 if( s.axis ==0 )else 0)
            
            self.sensorMatrix[x][y] = s.getId()
    
    def sensorsTimePass(self):
        for s in self.sensors:
            s.decreaseTimeLeft()

            
    def movement(self, pos):
        tempMat = self.sensorMatrix.copy()
        for s in self.sensors:
            x, y = pos
            xs, ys = s.pos

            if s.axis == 1 and xs <= x:
                s.activation()
                if s.active:
                    _, col = self.size
                    tempMat[xs+1, 1:]=np.full(col, 1)
                
            elif s.axis == 0 and ys <= y :
                s.activation()
                if s.active:
                    col, _ = self.size
                    tempMat[1:, ys+1]=np.full(col, 1)
        
        #print(tempMat)
        
        return 
    
    def getSensors(self):
        return self.sensors

#This is a prototype of the localization function we will use in data analisys
#Used by printData only
def vote(a):
    sens = a.getSensors()
    tempMat = np.zeros((a.monitorMatrix.shape))
    x, y = a.size
    for s in sens:
        xs, ys = s.pos
        if s.active:
            if s.axis == 1:
                _, col = a.size
                for i in range(xs, x):
                    tempMat[i, :]+=np.ones(col)
            else:
                col, _ = a.size
                for i in range(ys, y):
                    tempMat[:, i]+=np.ones(col)

        else:
            if s.axis == 1:
                _, col = a.size
                for i in range(xs, x):
                    tempMat[i, :]-=np.ones(col)
            else:
                col, _ = a.size
                for i in range(ys, y):
                    tempMat[:, i]-=np.ones(col)

                    
    count = 0
    maxTuple = (0,0)
    maxVal = 0
    
    argMax = np.argmax(tempMat, axis=1)
    for i in tempMat:
        temp = i[(argMax[count])]
        maxTuple, maxVal = (((count, argMax[count]), temp) if temp>maxVal else (maxTuple, maxVal))
        count+=1

    return tempMat, maxTuple

#Save image representation of moviment possible position based on "vote"
#Helpful with visualization of scripts and debugging
def printData(data, step):
    val1, val2 = data.shape
    fig = plt.figure()
    plt.rcParams["figure.figsize"] = (10,10)
    plt.rcParams['xtick.labelsize'] = 10
    plt.rcParams['ytick.labelsize'] = 10
    plt.imshow(data)
    ax = plt.gca()
    ax.set_xticks(np.arange(0, val2, 0.5))
    ax.set_yticks(np.arange(0, val1, 0.5))
    ax.set_xticklabels(np.arange( 0.5,val2+0.5, 0.5))
    ax.set_yticklabels([ i*0.5 for i in range((val1*2), 0, -1)])
    plt.grid(which='both', axis='both', linestyle='-', color='k', linewidth=1)
    #plt.show()
    plt.draw()
    fig.savefig("step_{}.png".format(step+1), dpi=70)
    plt.close()

#Save the actual room of each sensor
def sensorClasses(house):
    correctClass = open("correct.csv", "a")
    correctClass.write("id;class\n")
    for key in house.keys():
        for s in house[key]["room"].getSensors():
            correctClass.write(str(s.getId())+";"+key+"\n")

#Save sensors data to a CSV file, receive the ambient definition
def writeCSV(house):
    exist = os.path.exists("data.csv")
    csv_file = open("data.csv", "a") 
    sensorsDict = {}

    for key in house.keys():
        for s in house[key]["room"].getSensors():
            sensorsDict[s.getId()] = int(s.getActive())

    orderedKeys = sort(list(sensorsDict.keys()))

    if not exist:
        csv_file.write(str(orderedKeys[0]))
        for key in orderedKeys[1:]:
            csv_file.write("; "+str(key))
        csv_file.write("\n")
        
    csv_file.write(str(sensorsDict[orderedKeys[0]]))
    for key in orderedKeys[1:]:
        csv_file.write("; "+str(sensorsDict[key]))
    csv_file.write("\n")


class controlador:
    def __init__(self):

        #Ambient definition, in future will be made by reading a file
        self.house = {

            "sala" : {
                "room": sala((4,3.5), 0.5),
                "links":{
                    '(0, 6)': 'corredor',
                    '(1, 6)': 'corredor'
                }
            },
            "quarto1" : {
                "room": sala((3,3), 0.5),
                "links":{
                    '(0, 5)': 'corredor'
                }
            },

            "quarto2" : {
                "room": sala((3,4), 0.5),
                "links":{
                    '(0, 0)': 'corredor'
                }
            },

            "quarto3" : {
                "room": sala((3,3), 0.5),
                "links":{
                    '(5, 0)': 'corredor'
                }
            },

            "corredor" : {
                "room": sala((1,4.5), 0.5),
                "links":{
                    '(0, 0)': 'sala',
                    '(1, 0)': 'sala',
                    '(1, 5)': 'quarto1',
                    '(1, 7)': 'quarto2',
                    '(1, 8)': 'quarto2',
                    '(0, 2)': 'cozinha',
                    '(0, 3)': 'banheiro1',
                    '(0, 6)': 'banheiro2',
                }
            },

            "cozinha" : {
                "room": sala((2, 3), 0.5),
                "links":{
                    '(4, 5)': 'corredor',
                }
            },
            "varanda" : {
                "room": sala((2,2), 0.5),
                "links":{
                    '(3, 3)': 'sala'
                }
            },
            "banheiro1" : {
                "room": sala((1.5,2), 0.5),
                "links":{
                    '(2, 0)': 'corredor'
                }
            },
            "banheiro2" : {
                "room": sala((1.5,2), 0.5),
                "links":{
                    '(2, 0)': 'corredor'
                }
            }
    }
        
    def moviment(self, room, pos):
        self.house[room]["room"].movement(pos) 
        
    
    def rand_moviment(self, steps, init_room, pos):
        ang = 0
        
        #Decision of the next step direction 
        def next_ang(ang):
            rand = random.random()
            if(rand<0.55): 
                return ang
            elif(rand>=0.55 and rand<0.7): 
                return (ang-1)%8
            elif(rand>=0.7 and rand<0.85): 
                return (ang+1)%8
            elif(rand>=0.85 and rand<0.9):
                return (ang-2)%8
            elif(rand>=0.9 and rand<0.95): 
                return (ang+2)%8
            elif(rand>=0.95 and rand<0.97): 
                return (ang-3)%8
            elif(rand>=0.97 and rand<0.99): 
                return (ang+3)%8
            elif(rand>=0.99 ): return (ang+4)%8
        
        def next_step(ang, pos):
            if(ang==0): 
                return tuple(map( lambda x, y: x+y, pos, (0,1) ))
            elif(ang==1): 
                return tuple(map( lambda x, y: x+y, pos, (-1,1) ))
            elif(ang==2): 
                return tuple(map( lambda x, y: x+y, pos, (-1,0) ))
            elif(ang==3):
                return tuple(map( lambda x, y: x+y, pos, (-1,-1) ))
            elif(ang==4): 
                return tuple(map( lambda x, y: x+y, pos, (0,-1) ))
            elif(ang==5): 
                return tuple(map( lambda x, y: x+y, pos, (1,-1) ))
            elif(ang==6): 
                return tuple(map( lambda x, y: x+y, pos, (1,0) ))
            elif(ang==7 ): 
                return tuple(map( lambda x, y: x+y, pos, (1,1) ))
        
        total = steps
        while(steps>0):
        
            ang = next_ang(ang)
            posNew = next_step(ang, pos)

            a, b = posNew
            temp = self.house[init_room]["room"].monitorMatrix.shape
            k1, k2 = temp
            if a>=k1 or b>=k2 or a<0 or b<0:
                ang = (ang+4)%8
                posNew = next_step(ang, pos)
            
            pos= posNew
            
            try:
                self.house[init_room]["room"].movement(pos)
                data, posi = vote(self.house[init_room]["room"])
                printData(data, (total-steps))
            except:
                print("Movementation fail in random walk")

            steps-=1

    def parser(selsf, script):
        temp_script = []
        for i in script:
            posI, posJ, steps = i
            temp_script+= ([(posI, posJ)]*steps)
        return  temp_script

    def scripted_moviment(self, steps, room):
        count = 0
        chegando=False
        sensorClasses(self.house)
        steps = self.parser(steps)
        for i in steps:
            for key in self.house.keys():
                self.house[key]["room"].sensorsTimePass()
            
            try:
                self.house[room]["room"].movement(i)
                writeCSV(self.house)
                data, posi = vote(self.house[room]["room"])
                printData(data, count)
            except:
                print("Movementation fail in scripted walk!")
            
            #In a brief future the transition scheme will be changed so it can be chosen to be taken in script
            if str(i) in self.house[room]["links"].keys() and chegando!=True:
                room = self.house[room]["links"][str(i)]
                chegando = True
            elif(chegando == True):
                chegando = False    
            count+=1


controller = controlador ()

script = [(3,0,1),(2,1,3),(2,2,2),(1,3,3),(1,4,1),(0,5,1), (1, 5,1), (1,6,2), (1,7,3), (0,0,1), (1,1,1), (2,2,1)]

#script1 = [(0,0),(1,1),(2,2),(3,3),(4,4),(5,5),(6,6),(7,7),(7,8),(7,9)]

controller.scripted_moviment(script, "quarto1")
