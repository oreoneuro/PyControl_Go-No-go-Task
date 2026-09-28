#--------------------------Go/No-Go Stage 2: Center Poke Training--------------------------
# Adapted from KaetzelLab/Operant-Box-Code
#   https://github.com/KaetzelLab/Operant-Box-Code
# Original authors: Sampath K. T. Kapanaiah, Dennis Kaetzel (Kaetzel Lab)
#
# Modified by Soyeon Lee, Laboratory of Neuroscience, KOREA UNIVERSITY, 2026-09
#
# Purpose:
#   - train animals to respond to illumination of the center nose-poke port
#   - establish the center-poke -> reward-port sequence before Go/No-Go training
#
# Protocol:
#   - each trial begins with illumination of the center port (poke 3)
#   - a poke at the illuminated center port turns off the center-port LED
#   - the reward-port LED is then illuminated
#   - a reward-port poke triggers reward delivery
#   - only one reward is delivered per trial
#   - after reward-port exit, an inter-trial interval begins
#   - following the ITI, the next trial begins
#
# Notes:
#   - house light is not used as a trial-start cue
#   - house light is reserved for penalty signaling in later training stages
#   - ports other than the center port are physically covered during this stage
#
# Modifications:
#   - center port (poke 3) used as the response port
#   - reward delivery triggered by reward-port poke
#   - one reward delivered per trial
#   - syringe pump parameters adjusted for the current hardware
#   - periodic pump step compensation added
#   - session terminates after the maximum number of trials or session time limit


from pyControl.utility import *
import hardware_definition as hw


# ---------------- States and events ----------------

states = [
    'center_poke',
    'reward',
    'iti'
]

events = [
    'session_timer',
    'poke_3',
    'poke_6',
    'poke_6_out'
]

initial_state = 'center_poke'


# ---------------- Training parameters ----------------

v.ITI_dur = 5 * second          # Interval between completed trials
v.session_dur = 30 * minute     # Maximum session duration
v.max_trial = 50                # Maximum number of trials

v.current_trial = 0
v.reward_delivered = False


# ---------------- Pump parameters ----------------

v.steps_rate = 250
v.n_steps = 67


# ---------------- Pump compensation ----------------

v.reward_count = 0
v.comp_count = 0
v.comp_period = 12
v.comp_list = [2, 6, 10]
v.comp_batch = 2


# ---------------- Run start/end ----------------

def run_start():

    set_timer('session_timer', v.session_dur)

    # House light remains OFF during normal Stage 2 trials.
    hw.house_light.off()

    print('Go/No-Go Stage 2 Start')


def run_end():

    hw.off()
    hw.house_light.off()


# ---------------- Reward delivery ----------------

def deliver_reward():

    print('Reward_delivered')

    v.reward_count += 1
    v.comp_count += 1

    k = v.comp_count % v.comp_period

    rate2 = v.steps_rate
    v.main_steps = v.n_steps

    # Pump-step compensation
    if k in v.comp_list:
        v.main_steps = v.n_steps * v.comp_batch
        v.comp_count += (v.comp_batch - 1)
        rate2 = v.steps_rate * 2

    print(
        'COMP: count={}, comp_count={}, period={}, main_steps={}'.format(
            v.reward_count,
            v.comp_count,
            k,
            v.main_steps
        )
    )

    hw.syringe_pump.backward(rate2, v.main_steps)


# ---------------- Center-poke state ----------------

def center_poke(event):

    if event == 'entry':

        v.current_trial += 1

        print('Trial: {}'.format(v.current_trial))
        print('Center_poke_LED_ON')

        # Trial begins with illumination of the center port.
        hw.five_poke.poke_3.LED.on()


    elif event == 'poke_3':

        print('Center_poke_response')

        # Successful center poke -> reward becomes available.
        goto_state('reward')


    elif event == 'exit':

        hw.five_poke.poke_3.LED.off()


# ---------------- Reward state ----------------

def reward(event):

    if event == 'entry':

        print('Reward_available')

        hw.reward_port.LED.on()

        # Allow one reward in the new trial.
        v.reward_delivered = False


    elif event == 'poke_6':

        if not v.reward_delivered:

            deliver_reward()
            v.reward_delivered = True


    elif event == 'poke_6_out':

        if v.reward_delivered:

            goto_state('iti')


    elif event == 'exit':

        hw.reward_port.LED.off()


# ---------------- Inter-trial interval ----------------

def iti(event):

    if event == 'entry':

        print('ITI_start')
        print('ITI_dur: {}'.format(v.ITI_dur))

        # End session if maximum trial count has been reached.
        if v.current_trial >= v.max_trial:
            stop_framework()

        else:
            timed_goto_state(
                'center_poke',
                v.ITI_dur
            )


# ---------------- State-independent behavior ----------------

def all_states(event):

    if event == 'session_timer':

        print('Session_End')
        stop_framework()