"""
This demo aims to help player running system quickly by using the pypi library simple-emualtor https://pypi.org/project/simple-emulator/.
"""
from simple_emulator import CongestionControl

# We provided a simple algorithms about block selection to help you being familiar with this competition.
# In this example, it will select the block according to block's created time first and radio of rest life time to deadline secondly.
from simple_emulator import BlockSelection

EVENT_TYPE_FINISHED='F'
EVENT_TYPE_DROP='D'
EVENT_TYPE_TEMP='T'

MAX_BW = 200.0 * 1000 * 1000 * 8
MAX_PRIO = 3
# Your solution should include block selection and bandwidth estimator.
# We recommend you to achieve it by inherit the objects we provided and overwritten necessary method.
class MySolution(BlockSelection, CongestionControl):

    def __init__(self):
        super().__init__()
        # base parameters in CongestionControl

        # the value of congestion window
        self.cwnd = 1
        # the value of sending rate
        self.send_rate = float("inf")
        # the value of pacing rate
        self.pacing_rate = float("inf")
        # use cwnd
        self.USE_CWND=True

        # for reno
        self.ssthresh = float("inf")
        self.curr_state = "slow_start"
        self.states = ["slow_start", "congestion_avoidance", "fast_recovery"]
        # the number of lost packets
        self.drop_nums = 0
        # the number of acknowledgement packets
        self.ack_nums = 0

        # current time
        self.cur_time = -1
        # the value of cwnd at last packet event
        self.last_cwnd = 0
        # the number of lost packets received at the current moment
        self.instant_drop_nums = 0

        # select block parameters
        self.interval_pkt_num = 0
        self.interval_start_time = 0
        self.interval_send_num = 0

        self.cur_rate = float("inf")

        self.rtt = -10000.0
        self.rtt_update_time = 0
        self.last_block_id = -1

        self.ddl = 0
        self.size = 0
        self.prio = -1

    def select_block(self, cur_time, block_queue):
        '''
        The alogrithm to select the block which will be sended in next.
        :param cur_time: float
        :param block_queue: the list of Block.You can get more detail about Block in objects/block.py
        :return: int
        '''
        self.interval_send_num += 1

        if self.rtt > 0.0 and self.rtt_update_time + self.rtt < cur_time:
            self.rtt_update_time = cur_time
            self.rtt = -10000.0

        if len(block_queue) == 0:
            return -1

        min_weight: float = 10000000.0 
        min_weight_block_idx: int = -1

        ddl, size, prio = 0, 0, -1

        for idx, block in enumerate(block_queue):
            cur_block_info = block.block_info
            tmp_ddl = cur_block_info["Deadline"]
            passed_time = cur_time - cur_block_info["Create_time"] 
            tmp_size = cur_block_info["Size"]
            cur_sending_rate = self.cur_rate

            remaining_time = tmp_ddl - passed_time - self.rtt - ((tmp_size * 8.0) / cur_sending_rate)
            if remaining_time >= 0.0:
                tmp_prio = cur_block_info["Priority"]
                weight = (1.0 * remaining_time / tmp_ddl) / (1 - 1.0 * tmp_prio / MAX_PRIO)
                if min_weight_block_idx == -1 or \
                    min_weight > weight or \
                    (min_weight == weight and tmp_size < block_queue[min_weight_block_idx].block_info["Size"]):

                    min_weight_block_idx = idx
                    min_weight = weight
                    ddl = tmp_ddl
                    prio = tmp_prio
                    size = tmp_size
        self.ddl = ddl
        self.size = size
        self.prio = prio

        self.last_block_id = min_weight_block_idx

        if min_weight_block_idx != -1:
            self.last_block_id = block_queue[min_weight_block_idx].block_info["Block_id"]
            return min_weight_block_idx
        else:
            return 0

    def on_packet_sent(self, cur_time):
        """
        The part of solution to update the states of the algorithm when sender need to send packet.
        """
        return super().on_packet_sent(cur_time)

    def cc_trigger(self, cur_time, event_info):
        """
        The part of algorithm to make congestion control, which will be call when sender get an event about acknowledge or lost from reciever.
        See more at https://github.com/AItransCompetition/simple_emulator/tree/master#congestion_control_algorithmpy.
        """

        event_type = event_info["event_type"]
        event_time = cur_time

        if self.cur_time < event_time:
            # initial parameters at a new moment
            self.last_cwnd = 0
            self.instant_drop_nums = 0

        # if packet is dropped
        if event_type == EVENT_TYPE_DROP:
            # dropping more than one packet at a same time is considered one event of packet loss 
            if self.instant_drop_nums > 0:
                return
            self.instant_drop_nums += 1
            # step into fast recovery state
            self.curr_state = self.states[2]
            self.drop_nums += 1
            # clear acknowledgement count
            self.ack_nums = 0
            # Ref 1 : For ensuring the event type, drop or ack?
            self.cur_time = event_time
            if self.last_cwnd > 0 and self.last_cwnd != self.cwnd:
                # rollback to the old value of cwnd caused by acknowledgment first
                self.cwnd = self.last_cwnd
                self.last_cwnd = 0

        # if packet is acknowledged
        elif event_type == EVENT_TYPE_FINISHED:
            # Ref 1
            if event_time <= self.cur_time:
                return
            self.cur_time = event_time
            self.last_cwnd = self.cwnd

            # increase the number of acknowledgement packets
            self.ack_nums += 1

            # update rtt
            if self.rtt < 0.0:
                self.rtt = event_info["packet_information_dict"]["Latency"]
            else:
                self.rtt = self.rtt * 0.8 + event_info["packet_information_dict"]["Latency"] * 0.2
            self.rtt_update_time = event_time
            # print(self.rtt)
            self.interval_pkt_num += 1
            # double cwnd in slow_start state
            if self.curr_state == self.states[0]:
                if self.ack_nums == self.cwnd:
                    self.cwnd *= 2
                    self.ack_nums = 0
                # step into congestion_avoidance state due to exceeding threshhold
                if self.cwnd >= self.ssthresh:
                    self.curr_state = self.states[1]

            # increase cwnd linearly in congestion_avoidance state
            elif self.curr_state == self.states[1]:
                if self.ack_nums == self.cwnd:
                    self.cwnd += 1
                    self.ack_nums = 0

        # reset threshhold and cwnd in fast_recovery state
        if self.curr_state == self.states[2]:
            self.ssthresh = max(self.cwnd // 2, 1)
            self.cwnd = self.ssthresh
            self.curr_state = self.states[1]
        self.cur_rate = self.send_rate
        # set cwnd or sending rate in sender
        return {
            "cwnd" : self.cwnd,
            "send_rate" : self.send_rate,
        }