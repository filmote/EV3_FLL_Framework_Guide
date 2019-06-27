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
from ev3dev2.sensor.lego import TouchSensor
from time import sleep

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

def createAction(name, motor, speed, seconds):

    action = {}
    action['name'] = name
    action['motor'] = motor
    action['speed'] = speed
    action['seconds'] = seconds

    return action

def launchStep(stop, action):

    if action.get('name') == 'onForSeconds':
        thread = threading.Thread(target=onForSeconds, args=(stop, action.get('motor'), action.get('speed'), action.get('seconds')))
        thread.start()
        return thread
    
    if action.get('name') == 'delayForSeconds':
        thread = threading.Thread(target=delayForSeconds, args=(stop, action.get('seconds')))
        thread.start()
        return thread

def main():

    threadPool = []
    actions = []
    stopProcessing = False
    
    largeMotor_Left = LargeMotor(OUTPUT_B)
    largeMotor_Right = LargeMotor(OUTPUT_C)
    mediumMotor = MediumMotor()
    ts = TouchSensor()
    
    action1 = createAction('onForSeconds', largeMotor_Left, 20, 4)
    action2 = createAction('onForSeconds', largeMotor_Right, 40, 3)
    action3 = createAction('delayForSeconds', None, None, 2)
    action4 = createAction('onForSeconds', mediumMotor, 10, 8)
    
    actionParallel = []
    actionParallel.append(action1)
    actionParallel.append(action2)
    
    actions.append(actionParallel)
    actions.append(action3)
    actions.append(action4)
    
    for action in actions:

        # are their multiple actions to execute in parallel?
        if isinstance(action, list):
    
            for subAction in action:
                thread = launchStep(lambda:stopProcessing, subAction)
                threadPool.append(thread)
    
        # is there a single action to execute?
        else:
            thread = launchStep(lambda:stopProcessing, action)
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

            sleep(0.25)

        # if the 'stopProcessing' flag has been set then break out of the program altogether
        if stopProcessing:
            break


main()