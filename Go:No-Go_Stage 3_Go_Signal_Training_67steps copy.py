#--------------------------Go/No-Go Stage 3: Go Signal Training--------------------------
# Adapted from KaetzelLab/Operant-Box-Code
#   https://github.com/KaetzelLab/Operant-Box-Code
# Original authors: Sampath K. T. Kapanaiah, Dennis Kaetzel (Kaetzel Lab)
#
# Modified by Soyeon Lee, Laboratory of Neuroscience, KOREA UNIVERSITY, 2026-09
#
# Purpose:
#   - train animals to respond to a Go signal
#   - establish the association between the Go cue and center-poke response
#   - prepare animals for subsequent Go/No-Go discrimination training
#
# Protocol:
#   - each trial is preceded by a 5-s inter-trial interval (ITI)
#   - after the ITI, poke 1, poke 2, and poke 3 LEDs are illuminated
#   - poke 1 + poke 2 illumination serves as the Go signal
#   - poke 3 serves as the response port
#   - the first 0.5 s after cue onset is a buffer period
#   - poke 3 responses during the buffer are recorded but have no consequence
#   - after the buffer, animals have a 2-s response window
#   - a poke at poke 3 during the response window is a correct Go response
#   - correct Go responses turn off the task LEDs and illuminate the reward port
#   - a reward-port poke triggers reward delivery
#   - failure to respond within the response window is scored as an omission
#   - omissions result in a 5-s house-light penalty followed by the normal ITI
#
# Notes:
#   - poke 1 + poke 2 constitute the Go signal
#   - poke 3 is illuminated together with the Go signal at trial onset
#   - house light is used only as a penalty signal
#   - session duration is 30 min
#
# ------------------------------------------------------------------------------


from pyControl.utility import *
import hardware_definition as hw


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

v.current_trial = 0
v.reward_delivered = False

# Behavioral counters
v.correct_go = 0
v.omission = 0
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


# ---------------- Run start/end ----------------

def run_start():

    set_timer('session_timer', v.session_dur)

    # House light is reserved for penalty.
    hw.house_light.off()

    # All task LEDs remain OFF during the initial ITI.
    hw.five_poke.poke_1.LED.off()
    hw.five_poke.poke_2.LED.off()
    hw.five_poke.poke_3.LED.off()
    hw.reward_port.LED.off()

    print('Go/No-Go Stage 3 Start')


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


# ---------------- Inter-trial interval ----------------

def iti(event):

    if event == 'entry':

        print('ITI_start')
        print('ITI_dur: {}'.format(v.ITI_dur))

        # All task-related lights are OFF during the ITI.
        hw.five_poke.poke_1.LED.off()
        hw.five_poke.poke_2.LED.off()
        hw.five_poke.poke_3.LED.off()
        hw.reward_port.LED.off()
        hw.house_light.off()

        # After the ITI, begin the next trial.
        timed_goto_state('buffer', v.ITI_dur)


# ---------------- Trial onset / buffer ----------------

def buffer(event):

    if event == 'entry':

        v.current_trial += 1

        print('Trial: {}'.format(v.current_trial))
        print('Go_signal_ON')
        print('Buffer_start')

        # Trial onset:
        # poke 1 + poke 2 = Go signal
        # poke 3 = response port
        hw.five_poke.poke_1.LED.on()
        hw.five_poke.poke_2.LED.on()
        hw.five_poke.poke_3.LED.on()

        # 0.5-s buffer before responses become valid.
        timed_goto_state('response', v.buffer_dur)


    elif event == 'poke_3':

        # Record early responses but impose no consequence.
        v.buffer_poke += 1

        print('Buffer_poke')
        print('Buffer_poke_count: {}'.format(v.buffer_poke))


# ---------------- Go response window ----------------

def response(event):

    if event == 'entry':

        print('Response_window_start')
        print('Response_window_dur: {}'.format(v.response_dur))

        # If no valid poke occurs within 2 s,
        # automatically transition to penalty.
        timed_goto_state('penalty', v.response_dur)


    elif event == 'poke_3':

        v.correct_go += 1

        print('Correct_Go')
        print('Correct_Go_count: {}'.format(v.correct_go))

        goto_state('reward')


    elif event == 'exit':

        # Cue and response-port LEDs turn off
        # as soon as the response window ends.
        hw.five_poke.poke_1.LED.off()
        hw.five_poke.poke_2.LED.off()
        hw.five_poke.poke_3.LED.off()


# ---------------- Reward state ----------------

def reward(event):

    if event == 'entry':

        print('Reward_available')

        # Go cue and center-port light are already OFF.
        # Illuminate only the reward port.
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


# ---------------- Omission penalty ----------------

def penalty(event):

    if event == 'entry':

        v.omission += 1

        print('Omission')
        print('Omission_count: {}'.format(v.omission))
        print('Penalty_start')

        # Ensure task LEDs are OFF.
        hw.five_poke.poke_1.LED.off()
        hw.five_poke.poke_2.LED.off()
        hw.five_poke.poke_3.LED.off()
        hw.reward_port.LED.off()

        # House light signals the penalty period.
        hw.house_light.on()

        timed_goto_state('iti', v.penalty_dur)


    elif event == 'exit':

        hw.house_light.off()

        print('Penalty_end')


# ---------------- State-independent behavior ----------------

def all_states(event):

    if event == 'session_timer':

        print('Session_End')

        print(
            'SUMMARY: trials={}, correct_go={}, omission={}, buffer_poke={}, rewards={}'.format(
                v.current_trial,
                v.correct_go,
                v.omission,
                v.buffer_poke,
                v.reward_count
            )
        )

        stop_framework()