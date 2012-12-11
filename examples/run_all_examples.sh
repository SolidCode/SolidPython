COMPILED_EXAMPLES=${PWD}/Compiled_examples

echo
# if COMPILED_EXAMPLES doesn't exist, create it.
if [ ! -e $COMPILED_EXAMPLES ]; 
     then mkdir $COMPILED_EXAMPLES;     
fi    
 
for py in *.py;
do python $py $COMPILED_EXAMPLES;  
echo;
done