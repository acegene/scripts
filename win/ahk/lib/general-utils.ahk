HasVal(array, val) {
	if !(IsObject(array)) || (array.Length() = 0)
		return 0
	for index, value in array
		if (value = val)
			return index
	return 0
}

SleepRandom(Sleep, min:=1.0, max:=1.2){
    Random, SleepRandom, min*Sleep, max*Sleep
    Sleep SleepRandom
}
