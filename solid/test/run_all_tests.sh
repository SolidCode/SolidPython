# Note that this file needs to be run from solid/test.  
for i in test_*.py;
do 
echo $i;
python $i;
echo
done
