#--------------------------Reward Port Habituation Protocol--------------------------
# Adapted from KaetzelLab/Operant-Box-Code
#   https://github.com/KaetzelLab/Operant-Box-Code
# Original authors: Sampath K. T. Kapanaiah, Dennis Kaetzel (Kaetzel Lab)
#
# Modified by Soyeon Lee, Laboratory of Neuroscience, KOREA UNIVERSITY, 2026-09
#
# Purpose:
#   - train animals to associate the illuminated reward port with reward availability
#   - establish reward-port responding before task-specific training
#   - used as the initial operant habituation stage for both 5-CSRTT and Go/No-Go tasks
#
# Protocol:
#   - the reward-port LED is illuminated
#   - a reward-port poke triggers reward delivery
#   - only one reward is delivered per trial
#   - after reward-port exit, the trial ends
#   - following the inter-trial interval, the next trial begins
#
# Modifications:
#   - reward delivery triggered by reward-port poke
#   - one reward delivered per trial
#   - syringe pump parameters adjusted for the current hardware
#   - periodic pump step compensation added
#   - session terminates after the maximum number of trials or the session time limit


from pyControl.utility import *
import hardware_definition as hw
import random

# States and events
states = ['start',
          'choice',
          'iti']

events = ['session_timer',
          'poke_6',
          'poke_6_out']

initial_state = 'start'

# ---------------- Variables ----------------

# Stage parameters
v.ITI_dur   = 15 * second
v.session_dur   = 20 * minute
v.max_trial = 100 
v.current_trial = 0
v.reward_delivered = False

# ---- Pump parameters ----
v.steps_rate    = 250
v.n_steps       = 67


# ---- Compensation variables (habituation과 동일) ----
v.reward_count = 0         # 실제 보상이 나온 수
v.comp_count = 0           # 보정을 위한 count
v.comp_period = 12         # 주기 설정(360도)
v.comp_list = [2, 6, 10]   # 한번에 6trial이 나오는 부분
v.comp_batch = 2           # 보정 trial

v.target = 0


# ---------------- Run start/end ----------------
def run_start():
    set_timer('session_timer', v.session_dur)
    hw.house_light.on()

def run_end():
    hw.off()
    hw.house_light.off()

# ---------------- helper: deliver reward with compensation ----------------
def deliver_reward():
    
    print('Reward_delivered')

    v.reward_count += 1
    v.comp_count += 1
    k = v.comp_count % v.comp_period


    rate2 = v.steps_rate
    v.main_steps = v.n_steps


    if k in v.comp_list:
        v.main_steps = v.n_steps * v.comp_batch
        v.comp_count += (v.comp_batch - 1)
        rate2 = v.steps_rate *2

    print('COMP: count={}, comp_count={}, period={}, main_steps={}'.format(
        v.reward_count, v.comp_count, k, v.main_steps))

    hw.syringe_pump.backward(rate2, v.main_steps)

# ---------------- State functions ----------------
def start(event):
    if event == 'entry':
        print('Reward Port Habituation Start')
        goto_state('choice')

def choice(event):
    if event == 'entry':
        v.current_trial += 1
        print('Trial: {}'.format(v.current_trial))

        hw.reward_port.LED.on()
        v.reward_delivered = False
        
    elif event == 'poke_6':
        if not v.reward_delivered:
            deliver_reward()
            v.reward_delivered = True

    elif event == 'poke_6_out':
        if v.reward_delivered:
            hw.reward_port.LED.off()
            if v.current_trial >= v.max_trial:
                stop_framework()
            else:
                goto_state('iti')


def iti(event):
    if event == 'entry':
        print('iti_start_time')
        print('iti_dur:{}'.format(v.ITI_dur))
        timed_goto_state('choice', v.ITI_dur)


# ---------------- State independent behavior ----------------
def all_states(event):
    if event == 'session_timer':
        print("Event Closing")
        stop_framework()

