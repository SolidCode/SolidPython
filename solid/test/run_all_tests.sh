for i in test_*.py;
do 
echo $i;
python $i;
echo
done
