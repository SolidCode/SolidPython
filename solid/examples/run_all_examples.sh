COMPILED_EXAMPLES=${PWD}/Compiled_examples

echo
# if COMPILED_EXAMPLES doesn't exist, create it.
if [ ! -e $COMPILED_EXAMPLES ]; 
     then mkdir $COMPILED_EXAMPLES;     
fi    
 
for py in *.py;
do 
    echo "===================================================";
    echo "python $py $COMPILED_EXAMPLES";
    python $py $COMPILED_EXAMPLES;  
    echo "===================================================";
echo
done 

# Note: mazebox example isn't included because it requires a 
# significant python package (pypng) to be installed. 
# Comments in examples/mazebox/mazebox_clean2_stable.py
# explain how to install pypng