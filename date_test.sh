#!/bin/bash

# let's get the date with ms precision, X seconds in the future, rounded to the nearest second

# hardcode a number of seconds in the future
seconds_in_future=10
echo -e "Seconds in future\\t: $seconds_in_future"

# get the current date
date_now=$(date +%s%3N)

# print the current date
echo -e "Current date\\t: $date_now"

# add the number of seconds in the future
date_future=$((date_now + seconds_in_future * 1000))

# print the future date
echo -e "Future date\\t: $date_future"

# round to the nearest second
date_rounded=$(( (date_future + 500) / 1000 * 1000 ))

# print the rounded date
echo -e "Rounded date\\t: $date_rounded"