"""
Embedded Python Blocks:

Each time this file is saved, GRC will instantiate the first class it finds
to get ports and parameters of your block. The arguments to __init__  will
be the parameters. All of them are required to have default values!
"""

import numpy as np
import os
from gnuradio import gr
from datetime import datetime

class blk(gr.sync_block):  # other base classes are basic_block, decim_block, interp_block
    def __init__(self, samples_per_file=100000, samples_to_discard=300000, output_dir='~/iq_out', satid='noa'):
        gr.sync_block.__init__(self,
            name='File Splitter',
            in_sig=[np.complex64],
            out_sig=None)
        
        self.file_count = 1
        self.samples_per_file = samples_per_file
        self.samples_to_discard = samples_to_discard
        self.output_dir=output_dir
        self.satid=satid
        self.current_samples = 0
        self.state = 'save'
        self.directory = os.path.expanduser(output_dir)
        
        if not os.path.exists(self.directory):
            os.makedirs(self.directory)
        now=datetime.now()
        self.current_time=now.strftime("%Y%m%d-%H%M%S")
        self.file = open(os.path.join(self.directory, f"{self.satid}_{self.current_time}.float32"), "wb")

    def work(self, input_items, output_items):
        in0 = input_items[0]
        
        if self.state == 'save':
            # Determine the number of samples to save in this work call
            samples_to_write = min(len(in0), self.samples_per_file - self.current_samples)
            
            # Write the samples to the file
            self.file.write(in0[:samples_to_write].tobytes())
            self.current_samples += samples_to_write
            
            # Check if we have reached the limit for samples_per_file
            if self.current_samples >= self.samples_per_file:
                self.file.close()
                self.file_count += 1
                now=datetime.now()
                self.current_time=now.strftime("%Y%m%d-%H%M%S")
                self.file = open(os.path.join(self.directory, f"{self.satid}_{self.current_time}.float32"), "wb")
                self.current_samples = 0
                self.state = 'discard'
            
            return samples_to_write
        
        elif self.state == 'discard':
            # Determine the number of samples to discard in this work call
            samples_to_discard = min(len(in0), self.samples_to_discard - self.current_samples)
            
            # Increment the sample counter without writing to the file
            self.current_samples += samples_to_discard
            
            # Check if we have reached the limit for samples_to_discard
            if self.current_samples >= self.samples_to_discard:
                self.current_samples = 0
                self.state = 'save'
            
            return samples_to_discard
