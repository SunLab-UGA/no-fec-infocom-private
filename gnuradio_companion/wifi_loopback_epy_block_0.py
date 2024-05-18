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
    """This block looks for a (key . value) pair to filter from a PMT message."""

    def __init__(self, key=""):  # only default arguments here
        """arguments to this function show up as parameters in GRC"""
        gr.basic_block.__init__(
            self,
            name="PMT Filter",   # will show up in GRC
            in_sig=[],
            out_sig=[]
        )
        # if an attribute with the same name as a parameter is found,
        # a callback is registered (properties work, too).
        self.PMT_KEY = key

        # message input port definition
        self.in_mess = 'in'
        self.message_port_register_in(pmt.intern(self.in_mess))
        self.set_msg_handler(pmt.intern(self.in_mess), self.handler)

        # message output port definition
        self.out_mess = 'out'
        self.message_port_register_out(pmt.intern(self.out_mess))

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
        print(f"PMT FILTER: Received message")
        # try to get the value from the message
        value = pmt.pmt_to_python.pmt_to_python(msg)
        # parse the message for the key
        for v in value: # iterate through the message
            # print(f"value: {v}")
            for k in v:
                # print(f"key: {k}")
                if k == self.PMT_KEY:
                    value = v[k]
                    break
            # if v == self.PMT_KEY:
            # value = value[self.PMT_KEY]

        # print(f"Message: {value}")
        if value is not None:
            # if the key exists, output it as a new message
            # make new message
            key = pmt.to_pmt(self.PMT_KEY)
            value = pmt.to_pmt(value)
            msg = pmt.cons(key, value)
            # a = pmt.make_dict()
            # a = pmt.dict_add(a, self.PMT_KEY, value)
            self.message_port_pub(pmt.intern(self.out_mess), msg)
        else:
            print(f"ERROR: Key {self.PMT_KEY} not found in message")
        

