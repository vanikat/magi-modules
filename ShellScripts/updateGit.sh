#!/bin/bash
#delete magi-modules
echo ~-~-~Deleting Magi-Modules~-~-~
rm -r -f magi-modules
git clone https://github.com/rning/magi-modules
echo ~-~-~Now in Magi-Modules Directory~-~-~
cd magi-modules
