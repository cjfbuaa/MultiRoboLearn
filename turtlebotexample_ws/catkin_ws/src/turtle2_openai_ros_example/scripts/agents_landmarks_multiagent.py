#!/usr/bin/env python


import rospy
# from gym import spaces
import gym
import time
# import qlearn
from gym import wrappers
# ROS packages required
import rospy
import rospkg
# import our training environment
from openai_ros.robot_envs import multiagent_turtlebot2_env
from openai_ros.task_envs.turtlebot2 import multiagent_turtlebot2_goal

import numpy as np
import os
import random
import argparse
import pandas as pd
# from environments.agents_landmarks.env import agentslandmarks
from dqn_agent import Agent
import glob

ARG_LIST = ['learning_rate', 'optimizer', 'memory_capacity', 'batch_size', 'target_frequency', 'maximum_exploration',
            'max_timestep', 'first_step_memory', 'replay_steps', 'number_nodes', 'target_type', 'memory',
            'prioritization_scale', 'dueling', 'agents_number']


def is_in_desired_position(desired_point, current_position, epsilon=0.20):
    """
    It return True if the current position is similar to the desired poistion
    """

    is_in_desired_pos = False

    x_pos_plus = desired_point.x + epsilon
    x_pos_minus = desired_point.x - epsilon
    y_pos_plus = desired_point.y + epsilon
    y_pos_minus = desired_point.y - epsilon

    x_current = current_position.x
    y_current = current_position.y

    x_pos_are_close = (x_current <= x_pos_plus) and (x_current > x_pos_minus)
    y_pos_are_close = (y_current <= y_pos_plus) and (y_current > y_pos_minus)

    is_in_desired_pos = x_pos_are_close and y_pos_are_close

    return is_in_desired_pos


def get_name_brain(args, idx):

    file_name_str = '_'.join([x for x in args])

    return '/home/junfeng/pycharmproject/results_agents_landmarks/weights_files/' + file_name_str + '_' + str(idx) + '.h5'


def get_name_rewards(args):

    file_name_str = '_'.join([x for x in ARG_LIST])

    return '/home/junfeng/pycharmproject/results_agents_landmarks/rewards_files/' + file_name_str + '.csv'


def get_name_timesteps(args):

    file_name_str = '_'.join([x for x in ARG_LIST])

    return '/home/junfeng/pycharmproject/results_agents_landmarks/timesteps_files/' + file_name_str + '.csv'

def get_name_successrate(args):

    file_name_str = '_'.join([x for x in ARG_LIST])

    return '/home/junfeng/pycharmproject/results_agents_landmarks/successrate_files/' + file_name_str + '.csv'


def run(agents, file1, file2, file3, filling_steps, episodes_number, max_random_moves, max_ts, steps_b_updates, marobot1_desired_point, marobot2_desired_point, marobot3_desired_point):
    total_step = 0
    rewards_list = []
    timesteps_list = []
    success_list = []
    max_score = -10000
    test = False
    for episode_num in range(episodes_number):
        state = env.reset()
        random_moves = random.randint(0, max_random_moves)
        print("initial state is:", state)
        print("epsiode number is:", episode_num)

        # create randomness in initial state
        for _ in range(random_moves):
            actions = [_ for _ in range(len(agents))]
            state, _, _ = env.step(actions)

        # converting list of positions to an array
        # for a series of data transformation, transfer multi list to single list
        # state includes three parts: position and laser and position vector
        position_vector_1 = [state[0][0][0]-6,state[0][0][1]-6]
        position_vector_2 = [state[1][0][0]-1,state[1][0][1]-7]
        position_vector_3 = [state[2][0][0]+2,state[2][0][1]+3]

        # state = state[0][0]+state[0][1]+state[1][0]+state[1][1]+state[2][0]+state[2][1]+position_vector_1+position_vector_2+position_vector_3
        # for each agent, every agent's state is:
        state_1 = state[0][0]+state[0][1]+state[1][0]+state[1][1]+state[2][0]+state[2][1]+position_vector_1
        state_2 = state[0][0]+state[0][1]+state[1][0]+state[1][1]+state[2][0]+state[2][1]+position_vector_2
        state_3 = state[0][0]+state[0][1]+state[1][0]+state[1][1]+state[2][0]+state[2][1]+position_vector_3
        # print("state type is:",type(state))
        # print("state lenth is:",len(state))
        # print("state is:",state)

        # state type transfer into the certain type can be recognized by the algorithms
        # ######state = np.asarray(state).astype(np.float32) delete
        # state = np.asarray(state)
        # state = state.ravel()

        state_1 = np.asarray(state_1)
        state_1 = state_1.ravel()

        state_2 = np.asarray(state_2)
        state_2 = state_2.ravel()

        state_3 = np.asarray(state_3)
        state_3 = state_3.ravel()

        state_all = [state_1, state_2, state_3]


        # print("state type is:", type(state))
        # print("Initial state is:", state)
        # print("State shape is:", len(state))
        # print("Convert numpy to list is:", state.tolist())
        # print("Episode_num is:", episode_num)

        dones = False # refer to all the robots reach the desired points and whether end given episode
        reward_all = 0
        time_step = 0
        done = [False,False,False]
        while not dones and time_step < max_ts:

            # if self.render:
            #     self.env.render()
            print("time step number is:", time_step)

            actions = []
            i = -1
            for agent in agents:
                # actions.append(agent.greedy_actor(state))
                i = i + 1
                actions.append(agent.greedy_actor(state_all[i]))
            # decide each agent whether done, decide whether stop training
            index = [i for i in range(len(done)) if done[i] == True]
            for i in index:
                actions[i] = 4
            print("acations are:", actions)

            next_state, reward, done, info = env.step(actions)
            print("Env done are:", done)
            print("next_state is:", next_state)

            # if time_step >= 99:
            #     done = [False, False, False]
            dones = done[0] and done[1] and done[2]
            #state includes three parts: position and laser and position vector
            position_vector_1 = [next_state[0][0][0] - 6, next_state[0][0][1] - 6]
            position_vector_2 = [next_state[1][0][0] - 1, next_state[1][0][1] - 7]
            position_vector_3 = [next_state[2][0][0] + 2, next_state[2][0][1] + 3]

            # next_state = next_state[0][0] + next_state[0][1] + next_state[1][0] + next_state[1][1] + next_state[2][0] + next_state[2][1] + position_vector_1 + position_vector_2 + position_vector_3
            # converting list of positions to an array
            # next_state = next_state[0][0] + next_state[0][1] + next_state[1][0] + next_state[1][1] + next_state[2][0] + next_state[2][1]
            # #####next_state = np.asarray(next_state).astype(np.float32)
            # next_state = np.asarray(next_state)
            # next_state = next_state.ravel()

            next_state_1 = next_state[0][0] + next_state[0][1] + next_state[1][0] + next_state[1][1] + next_state[2][0] + next_state[2][1] + position_vector_1
            next_state_2 = next_state[0][0] + next_state[0][1] + next_state[1][0] + next_state[1][1] + next_state[2][0] + next_state[2][1] + position_vector_2
            next_state_3 = next_state[0][0] + next_state[0][1] + next_state[1][0] + next_state[1][1] + next_state[2][0] + next_state[2][1] + position_vector_3

            next_state_1 = np.asarray(next_state_1)
            next_state_1 = next_state_1.ravel()

            next_state_2 = np.asarray(next_state_2)
            next_state_2 = next_state_2.ravel()

            next_state_3 = np.asarray(next_state_3)
            next_state_3 = next_state_3.ravel()

            next_state_all = [next_state_1, next_state_2, next_state_3]
            # print("next_state is:", next_state)

            # if not test:
            #     for agent in agents:
            #         agent.observe((state, actions, reward, next_state, dones))
            #         if total_step >= filling_steps:
            #             agent.decay_epsilon()
            #             if time_step % steps_b_updates == 0:
            #                 agent.replay()
            #             agent.update_target_model()

            if not test:
                i = -1
                for agent in agents:
                    i = i + 1
                    state = state_all[i]
                    next_state = next_state_all[i]
                    agent.observe((state, actions, reward, next_state, dones))
                    if total_step >= filling_steps:
                        agent.decay_epsilon()
                        if time_step % steps_b_updates == 0:
                            agent.replay()
                        agent.update_target_model()

            total_step += 1
            time_step += 1
            # state = next_state
            state_1 = next_state_1
            state_2 = next_state_2
            state_3 = next_state_3
            reward_all += reward

            # in each episode, we will decide if each agent reach desired point and calculate success rate
            if dones == True or time_step >= max_ts:
                current_position_1 = Point()
                current_position_2 = Point()
                current_position_3 = Point()
                # for marobot1:
                current_position_1.x = observations[0][0][0]
                current_position_1.y = observations[0][0][1]
                current_position_1.z = 0.0

                # for marobot2:
                current_position_2.x = observations[1][0][0]
                current_position_2.y = observations[1][0][1]
                current_position_2.z = 0.0

                # for marobot3:
                current_position_3.x = observations[2][0][0]
                current_position_3.y = observations[2][0][1]
                current_position_3.z = 0.0

                # MAX_X = 10.0
                # MIN_X = -10.0
                # MAX_Y = 10.0
                # MIN_Y = -10.0

                desired_current_position = {str(current_position_1): marobot1_desired_point,
                                            str(current_position_2): marobot2_desired_point,
                                            str(current_position_3): marobot3_desired_point}

                for current_position in [current_position_1, current_position_2, current_position_3]:

                    # We see if it got to the desired point
                    if is_in_desired_position(desired_current_position[str(current_position)],
                                                   current_position):
                        _episode_done = True

                    # sub_episode_done = sub_episode_done.append(self._episode_done)
                    sub_episode_done.append(_episode_done)

                _episode_dones = sub_episode_done[:]




        # if self.render:
            #     self.env.render()

        rewards_list.append(reward_all)
        timesteps_list.append(time_step)

        # we can calculate success rate whether each agent reach desired point
        success_percent = round(_episode_dones.count(True)/3.0,2)
        success_list.append(success_percent)


        print("Episode {p}, Score: {s}, Final Step: {t}, Goal: {g}".format(p=episode_num, s=reward_all,
                                                                           t=time_step, g=done))

        # if self.recorder:
        #     os.system("ffmpeg -r 2 -i ./results_agents_landmarks/snaps/%04d.png -b:v 40000 -minrate 40000 -maxrate 4000k -bufsize 1835k -c:v mjpeg -qscale:v 0 "
        #               + "./results_agents_landmarks/videos/{a1}_{a2}_{a3}_{a4}.avi".format(a1=self.num_agents,
        #                                                                                      a2=self.num_landmarks,
        #                                                                                      a3=self.game_mode,
        #                                                                                      a4=self.grid_size))
        #     files = glob.glob('./results_agents_landmarks/snaps/*')
        #     for f in files:
        #         os.remove(f)

        if not test:
            if episode_num % 100 == 0:
                df = pd.DataFrame(rewards_list, columns=['score'])
                df.to_csv(file1)

                df = pd.DataFrame(timesteps_list, columns=['steps'])
                df.to_csv(file2)

                if total_step >= filling_steps:
                    if reward_all > max_score:
                        for agent in agents:
                            agent.brain.save_model()
                        max_score = reward_all

            # record success rate
            df = pd.DataFrame(success_list, columns=['success_rate'])
            df.to_csv(file3)




if __name__ =="__main__":

    rospy.init_node('agents_landmarks_multiagent', anonymous=True, log_level=rospy.WARN)

    # parser = argparse.ArgumentParser()
    # DQN Parameters
    episodes_number = rospy.get_param("/turtlebot2/episode_number")
    max_ts = rospy.get_param("/turtlebot2/max_timestep")
    test = rospy.get_param("/turtlebot2/test")
    filling_steps = rospy.get_param("/turtlebot2/first_step_memory")
    steps_b_updates = rospy.get_param("/turtlebot2/replay_steps")
    max_random_moves = rospy.get_param("/turtlebot2/max_random_moves")
    num_agents = rospy.get_param("/turtlebot2/agents_number")
    dueling = rospy.get_param("/turtlebot2/dueling")
    os.environ['CUDA_VISIBLE_DEVICES'] = rospy.get_param("/turtlebot2/gpu_num")

    # DQN agent parameters(learning_rate,memory,memory_capacity,prioritization_scale,
    #                        target_type,target_frequency,maximum_exploration,batch_size,test)

    learning_rate = rospy.get_param("/turtlebot2/learning_rate")
    memory = rospy.get_param("/turtlebot2/memory")
    memory_capacity = rospy.get_param("/turtlebot2/memory_capacity")
    prioritization_scale = rospy.get_param("/turtlebot2/prioritization_scale")
    target_type = rospy.get_param("/turtlebot2/target_type")
    target_frequency = rospy.get_param("/turtlebot2/target_frequency")
    maximum_exploration = rospy.get_param("/turtlebot2/maximum_exploration")
    batch_size = rospy.get_param("/turtlebot2/batch_size")
    number_nodes = rospy.get_param("/turtlebot2/number_nodes")
    dueling = rospy.get_param("/turtlebot2/dueling")
    optimizer = rospy.get_param("/turtlebot2/optimizer")
    # self.test = rospy.get_param("/turtlebot2/test")
    # env = Environment(args)
    env = gym.make("MultiagentTurtleBot2-v0")
    rospy.loginfo("Gym environment done")
    state_size = rospy.get_param("/turtlebot2/n_observations")
    # action_space = env.env.action_space()
    action_space = rospy.get_param("/turtlebot2/n_actions")


    marobot1_desired_point = Point()
    marobot1_desired_point.x = rospy.get_param("/turtlebot2/marobot1/desired_pose/x")
    marobot1_desired_point.y = rospy.get_param("/turtlebot2/marobot1/desired_pose/y")
    marobot1_desired_point.z = rospy.get_param("/turtlebot2/marobot1/desired_pose/z")

    marobot2_desired_point = Point()
    marobot2_desired_point.x = rospy.get_param("/turtlebot2/marobot2/desired_pose/x")
    marobot2_desired_point.y = rospy.get_param("/turtlebot2/marobot2/desired_pose/y")
    marobot2_desired_point.z = rospy.get_param("/turtlebot2/marobot2/desired_pose/z")

    marobot3_desired_point = Point()
    marobot3_desired_point.x = rospy.get_param("/turtlebot2/marobot3/desired_pose/x")
    marobot3_desired_point.y = rospy.get_param("/turtlebot2/marobot3/desired_pose/y")
    marobot3_desired_point.z = rospy.get_param("/turtlebot2/marobot3/desired_pose/z")



    # Starts the main training loop: the one about the episodes to do;
    # in the main loop, next_state, state, reward, actions are "list" type


    all_agents = []
    for b_idx in range(num_agents):
        brain_file = get_name_brain(ARG_LIST, b_idx)
        all_agents.append(Agent(state_size, action_space, b_idx, brain_file, learning_rate, memory,
                                memory_capacity, prioritization_scale, target_type, target_frequency,
                                maximum_exploration, batch_size, test, number_nodes, dueling, optimizer))

    rewards_file = get_name_rewards(ARG_LIST)
    timesteps_file = get_name_timesteps(ARG_LIST)
    successrate_file = get_name_successrate(ARG_LIST)

    run(agents=all_agents, file1=rewards_file, file2=timesteps_file, file3=successrate_file, filling_steps=filling_steps, episodes_number=episodes_number,
        max_random_moves=max_random_moves, max_ts=max_ts, steps_b_updates=steps_b_updates, marobot1_desired_point=marobot1_desired_point, marobot2_desired_point=marobot2_desired_point, marobot3_desired_point=marobot3_desired_point)
