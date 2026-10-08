#--------------------------Go/No-Go Discrimination Task--------------------------
# Adapted from KaetzelLab/Operant-Box-Code
#   https://github.com/KaetzelLab/Operant-Box-Code
# Original authors: Sampath K. T. Kapanaiah, Dennis Kaetzel (Kaetzel Lab)
#
# Modified by Soyeon Lee, Laboratory of Neuroscience, KOREA UNIVERSITY, 2026-09
#
# Purpose:
#   - train animals to discriminate between Go and No-Go signals
#   - assess execution of a center-poke response during Go trials
#   - assess response inhibition during No-Go trials
#
# Protocol:
#   - each trial is preceded by a 5-s inter-trial interval (ITI)
#
#   Go trial:
#   - poke 1 + poke 2 + poke 3 LEDs are illuminated
#   - the first 0.5 s is a buffer period
#   - animals then have a 2-s response window
#   - a poke at poke 3 is scored as a Correct Go response
#   - Correct Go responses lead to reward availability
#   - failure to respond is scored as an Omission and results in penalty
#
#   No-Go trial:
#   - poke 3 + poke 4 + poke 5 LEDs are illuminated
#   - the first 0.5 s is a buffer period
#   - animals must withhold the poke-3 response during the following 2 s
#   - successful withholding is scored as Correct No-Go
#   - Correct No-Go trials are not rewarded and proceed directly to the ITI
#   - a poke at poke 3 is scored as a False Hit and results in penalty
#
#   Buffer responses:
#   - poke-3 responses during the 0.5-s buffer are recorded
#   - buffer responses have no programmed consequence
#
#   Penalty:
#   - the house light is illuminated for 5 s
#   - the penalty is followed by the normal ITI
#
# Notes:
#   - Go / No-Go probability can be modified using v.go_probability
#   - default Go : No-Go ratio = 50 : 50
#   - session duration = 30 min


from pyControl.utility import *
import hardware_definition as hw
import random


# ---------------- States and events ----------------

states = [
    'iti',
    'buffer',
    'response',
    'reward',
    'penalty'
]

events = [
    'session_timer',
    'response_timer',
    'poke_3',
    'poke_6',
    'poke_6_out'
]

initial_state = 'iti'


# ---------------- Training parameters ----------------

v.ITI_dur = 5 * second
v.buffer_dur = 0.5 * second
v.response_dur = 2 * second
v.penalty_dur = 5 * second
v.session_dur = 30 * minute


# ---------------- Trial probability ----------------

# Probability that the next trial will be a Go trial.
# 0.5 = 50% Go / 50% No-Go
#
# Examples:
# 0.7 = 70% Go / 30% No-Go
# 0.3 = 30% Go / 70% No-Go

v.go_probability = 0.5


# ---------------- Trial variables ----------------

v.current_trial = 0

# Trial type:
# 1 = Go
# 0 = No-Go
v.trial_type = 0

v.reward_delivered = False


# ---------------- Behavioral counters ----------------

v.go_trials = 0
v.nogo_trials = 0

v.correct_go = 0
v.omission = 0

v.correct_nogo = 0
v.false_hit = 0

v.buffer_poke = 0


# ---------------- Pump parameters ----------------

v.steps_rate = 250
v.n_steps = 67


# ---------------- Pump compensation ----------------

v.reward_count = 0
v.comp_count = 0
v.comp_period = 12
v.comp_list = [2, 6, 10]
v.comp_batch = 2

# ---------------- Feedback sound ---------------------
v.sound_feedback = True
v.correct_sound_ms = 60
v.error_sound_ms = 200
v.correct_volume = 10
v.error_volume = 30


# ---------------- Run start/end ----------------

def run_start():

    set_timer('session_timer', v.session_dur)

    # All task lights are OFF during the initial ITI.
    hw.five_poke.poke_1.LED.off()
    hw.five_poke.poke_2.LED.off()
    hw.five_poke.poke_3.LED.off()
    hw.five_poke.poke_4.LED.off()
    hw.five_poke.poke_5.LED.off()

    hw.reward_port.LED.off()
    hw.house_light.off()

    print('Go/No-Go Discrimination Task Start')


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

    hw.syringe_pump.backward(
        rate2,
        v.main_steps
    )


# ---------------- Inter-trial interval ----------------

def iti(event):

    if event == 'entry':

        print('ITI_start')
        print('ITI_dur: {}'.format(v.ITI_dur))

        # All trial-related LEDs OFF.
        hw.five_poke.poke_1.LED.off()
        hw.five_poke.poke_2.LED.off()
        hw.five_poke.poke_3.LED.off()
        hw.five_poke.poke_4.LED.off()
        hw.five_poke.poke_5.LED.off()

        hw.reward_port.LED.off()
        hw.house_light.off()

        # Start next trial after ITI.
        timed_goto_state(
            'buffer',
            v.ITI_dur
        )


# ---------------- Trial onset / buffer ----------------

def buffer(event):

    if event == 'entry':

        v.current_trial += 1

        print('Trial: {}'.format(v.current_trial))

        # Randomly select Go or No-Go trial.
        if random.random() < v.go_probability:

            v.trial_type = 1
            v.go_trials += 1

            print('Trial_type: GO')

            # Go signal = poke 1 + poke 2
            # poke 3 = response port
            hw.five_poke.poke_1.LED.on()
            hw.five_poke.poke_2.LED.on()
            hw.five_poke.poke_3.LED.on()

        else:

            v.trial_type = 0
            v.nogo_trials += 1

            print('Trial_type: NO_GO')

            # No-Go signal = poke 4 + poke 5
            # poke 3 = response port
            hw.five_poke.poke_3.LED.on()
            hw.five_poke.poke_4.LED.on()
            hw.five_poke.poke_5.LED.on()

        print('Buffer_start')

        # 0.5-s buffer.
        timed_goto_state(
            'response',
            v.buffer_dur
        )


    elif event == 'poke_3':

        # Record but ignore responses during the buffer.
        v.buffer_poke += 1

        print('Buffer_poke')

        if v.trial_type == 1:
            print('Buffer_poke_trial: GO')

        else:
            print('Buffer_poke_trial: NO_GO')


# ---------------- Response window ----------------

def response(event):

    if event == 'entry':

        print('Response_window_start')
        print(
            'Response_window_dur: {}'.format(
                v.response_dur
            )
        )

        set_timer(
            'response_timer',
            v.response_dur
        )


    elif event == 'poke_3':

        # ---------------- GO ----------------

        if v.trial_type == 1:

            v.correct_go += 1

            print('Correct_Go')
            print(
                'Correct_Go_count: {}'.format(
                    v.correct_go
                )
            )

            goto_state('reward')


        # ---------------- NO-GO ----------------

        else:

            v.false_hit += 1

            print('False_Hit')
            print(
                'False_Hit_count: {}'.format(
                    v.false_hit
                )
            )

            goto_state('penalty')


    elif event == 'response_timer':

        # ---------------- GO ----------------
        # No response = omission

        if v.trial_type == 1:

            v.omission += 1

            print('Omission')
            print(
                'Omission_count: {}'.format(
                    v.omission
                )
            )

            goto_state('penalty')


        # ---------------- NO-GO ----------------
        # No response = correct rejection

        else:

            v.correct_nogo += 1

            print('Correct_NoGo')
            print(
                'Correct_NoGo_count: {}'.format(
                    v.correct_nogo
                )
            )

            goto_state('iti')


    elif event == 'exit':

        # Turn off all trial cue LEDs.
        hw.five_poke.poke_1.LED.off()
        hw.five_poke.poke_2.LED.off()
        hw.five_poke.poke_3.LED.off()
        hw.five_poke.poke_4.LED.off()
        hw.five_poke.poke_5.LED.off()


# ---------------- Reward state ----------------

def reward(event):

    if event == 'entry':

        print('Reward_available')

        hw.reward_port.LED.on()

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


# ---------------- Penalty state ----------------

def penalty(event):

    if event == 'entry':

        print('Penalty_start')

        # All task LEDs OFF.
        hw.five_poke.poke_1.LED.off()
        hw.five_poke.poke_2.LED.off()
        hw.five_poke.poke_3.LED.off()
        hw.five_poke.poke_4.LED.off()
        hw.five_poke.poke_5.LED.off()

        hw.reward_port.LED.off()

        # House light signals penalty.
        hw.house_light.on()

        # Feedback tone for penalty.
        play_feedback(is_correct=True)

        timed_goto_state(
            'iti',
            v.penalty_dur
        )


    elif event == 'exit':

        hw.house_light.off()

        print('Penalty_end')


# ---------------- State-independent behavior ----------------

def all_states(event):

    if event == 'session_timer':

        print('Session_End')

        print(
            'SUMMARY: trials={}, '
            'go_trials={}, nogo_trials={}, '
            'correct_go={}, omission={}, '
            'correct_nogo={}, false_hit={}, '
            'buffer_poke={}, rewards={}'.format(
                v.current_trial,
                v.go_trials,
                v.nogo_trials,
                v.correct_go,
                v.omission,
                v.correct_nogo,
                v.false_hit,
                v.buffer_poke,
                v.reward_count
            )
        )

        stop_framework()
