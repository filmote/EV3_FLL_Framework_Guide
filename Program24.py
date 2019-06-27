#!/usr/bin/env python3
''' 
--------------------------------------------------------------------------------

Copyright (c) 2019, Simon Holmes
All rights reserved.

Redistribution and use in source and binary forms, with or without
modification, are permitted provided that the following conditions are met:

1. Redistributions of source code must retain the above copyright notice, this
   list of conditions and the following disclaimer.
2. Redistributions in binary form must reproduce the above copyright notice,
   this list of conditions and the following disclaimer in the documentation
   and/or other materials provided with the distribution.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE LIABLE FOR
ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
(INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND
ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
(INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

The views and conclusions contained in the software and documentation are those
of the authors and should not be interpreted as representing official policies,
either expressed or implied, of the FLL Robot Framework project.

--------------------------------------------------------------------------------
'''

from ev3dev2.motor import MediumMotor, LargeMotor, OUTPUT_B, OUTPUT_C
from ev3dev2.sensor.lego import TouchSensor, ColorSensor
from time import sleep

import xml.etree.ElementTree as ET
import threading
import time


def onForSeconds(stop, motor, speed, seconds):

    start_time = time.time()
    motor.on(speed, brake = True, block = False)

    while time.time() < start_time + seconds:

        # if we are stopping prematurely break out of loop 
        if stop():
            break

    motor.off()

def delayForSeconds(stop, seconds):

    start_time = time.time()

    while time.time() < start_time + seconds:

        if stop():
            break

def launchStep(stop, action):
    
    largeMotor_Left = LargeMotor(OUTPUT_B)
    largeMotor_Right = LargeMotor(OUTPUT_C)
    mediumMotor = MediumMotor()
    
    name = action.get('action')
    motor = action.get('motor')
    speed = float(action.get('speed'))
    seconds = float(action.get('seconds'))

    if name == 'onForSeconds':

        if (motor == "largeMotor_Left"):
            motorToUse = largeMotor_Left
        if (motor == "largeMotor_Right"):
            motorToUse = largeMotor_Right
        if (motor == "mediumMotor"):
            motorToUse = mediumMotor

        thread = threading.Thread(target=onForSeconds, args=(stop, motorToUse, speed, seconds))
        thread.start()
        return thread
    
    if name == 'delayForSeconds':
        thread = threading.Thread(target=delayForSeconds, args=(stop, seconds))
        thread.start()
        return thread


def main():
    
    threadPool = []
    stopProcessing = False
   
    ts = TouchSensor()
    cl = ColorSensor()

    # Load programs ..
    programsXML = ET.parse('Program24_programs.xml')
    programs = programsXML.getroot()
    
    while True:

        rgb = cl.raw

        for program in programs:

            programName = program.get('name')
            rProgram = int(program.get('r'))
            gProgram = int(program.get('g'))
            bProgram = int(program.get('b'))

            rColourSensor = rgb[0]
            gColourSensor = rgb[1]
            bColourSensor = rgb[2]

            if abs(rColourSensor - rProgram) < 20 and abs(gColourSensor - gProgram) < 20 and abs(bColourSensor - bProgram) < 20:

                fileName = program.get('fileName')
                
                # Load program into memory ..
                dataXML = ET.parse(fileName)
                steps = dataXML.getroot()

                for step in steps:
                        
                    action = step.get('action')

                    # are their multiple actions to execute in parallel?
                    if action == 'launchInParallel':
                        for subSteps in step:
                            thread = launchStep(lambda:stopProcessing, subSteps)
                            threadPool.append(thread)
                
                    # is there a single action to execute?
                    else:
                        thread = launchStep(lambda:stopProcessing, step)
                        threadPool.append(thread)


                    while not stopProcessing:

                        # remove any completed threads from the pool
                        for thread in threadPool:
                            if not thread.isAlive():
                                threadPool.remove(thread)

                        # if there are no threads running, exist the 'while' loop 
                        # and start the next action from the list 
                        if not threadPool:
                            break

                        # if the touch sensor is pressed then complete everything
                        if ts.is_pressed:
                            stopProcessing = True
                            break

                        sleep(0.25)

                    # if the 'stopProcessing' flag has been set then finish the step loop
                    if stopProcessing:
                        break


main()