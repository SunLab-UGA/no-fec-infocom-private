"""
Embedded Python Blocks:

Each time this file is saved, GRC will instantiate the first class it finds
to get ports and parameters of your block. The arguments to __init__  will
be the parameters. All of them are required to have default values!
"""

import numpy as np
from gnuradio import gr
import pmt


class blk(gr.basic_block):  # other base classes are basic_block, decim_block, interp_block
    """This block prints the full contents of a PMT message.
    WARNING: This block may print a lot of data to the terminal, and may slow down GRC.
    It's generally only used to debug the PMT messages"""

    def __init__(self):  # only default arguments here
        """arguments to this function show up as parameters in GRC"""
        gr.basic_block.__init__(
            self,
            name="PMT Finder",   # will show up in GRC
            in_sig=[],
            out_sig=[]
        )
        # if an attribute with the same name as a parameter is found,
        # a callback is registered (properties work, too).
        # self.print_values = print_values

        # message input port definition
        self.in_mess = 'in'
        self.message_port_register_in(pmt.intern(self.in_mess))
        self.set_msg_handler(pmt.intern(self.in_mess), self.handler)

        # message output port definition
        # self.out_mess = 'out'
        # self.message_port_register_out(pmt.intern(self.out_mess))

    def work(self, input_items, output_items):
        # output_items[0][:] = input_items[0] * self.example_param
        # return len(output_items[0])
        pass
    
    # def print_all_keys(pmt_dict, prefix=""):
    #     if pmt.is_dict(pmt_dict):
    #         keys = pmt.dict_keys(pmt_dict)
    #         for key in keys:
    #             key_name = pmt.symbol_to_string(key)
    #             full_key_name = prefix + key_name
    #             print(f"Key: {full_key_name}")
                
    #             # Recursively call the function for nested dictionaries
    #             sub_dict = pmt.dict_ref(pmt_dict, key)
    #             if pmt.is_dict(sub_dict):
    #                 # print_all_keys(sub_dict, prefix=full_key_name + ".")
    #                 pass

    def handler(self, msg):
        '''This is the handler for the message port'''
        print(f"PMT FINDER: Received message")
        value = pmt.pmt_to_python.pmt_to_python(msg)
        print(f"Message: {value}")
        # print_all_keys(msg)
        

