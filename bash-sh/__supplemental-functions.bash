#!/bin/bash
# This script is not necessarily meant to be ran, for notes and educational purposes

# set -o nounset # breaks on references to unfilled variables
# set -e # will cause the scipt to exit on certain types of errors it wouldnt normally

__yes_no_prompt() { # __yes_no_prompt "string to print as prompt" "string to print if answered no" && cmd-if-continue || cmd-if-not-yes
	local REGEX='^[Yy]$'
	echo; read -p "${1} " -n 1 -r; echo; ! [[ "${REPLY}" =~ ${REGEX} ]] && echo "${2}" && return 1; echo
}

__remove_and_sort_array_duplicates() { # GENRES_OUT=($(__remove_array_duplicates "${GENRES_OUT[@]}"))
	echo "${@}" | tr ' ' '\n' | sort -u | tr '\n' ' ' # might have problems with newline characters
}

__remove_array_duplicates(){
	local arr=("${@}"); local n="${#arr[@]}"
	for (( i=0; i<$((n-1)); i++ )); do
		for (( j=$((i+1)); j<$n; j++ )); do
			[[ "${arr[i]}" == "${arr[j]}" ]] && arr=(${arr[@]:0:$j} ${arr[@]:$((j+1))}) && ((j--)) && ((n--))
		done
	done
	echo ${arr[@]}
}

__source_if_found(){
	[[ -f "${1}" ]] || ! echo "file=${1} not found"
}

__rename_mv_operation(){ # __rename_mv_operation "${file_to_rename}" "${name_to_rename_file_to}"
local lhs="${1}"; local rhs="${2}"
[ -f "${2}" ] && echo "ERROR: mv ${lhs} -> ${rhs} failed as target exists already" && return 1
[[ "${suppress}" == 'true' ]] || ! echo "${1} -- old" || echo "${2} -- new"
[[ "${rename}" == 'true' ]] && mv -n "${1}" "${2}"
return 0
}

__dir_relative_to_absolute(){
local abs_dir="${1}"
# echo $(readlink -f $0)
# echo "${BASH_SOURCE[1]}"
[ -d "${abs_dir}" ] || return 1
abs_dir=$(cd -- "${abs_dir}"/ && printf '%s.' "$PWD"); abs_dir="${abs_dir%.}"
[[ "${abs_dir}" != */ ]] && abs_dir="${abs_dir}/" # add trailing slash
echo "${abs_dir}"
[ -d "${abs_dir}" ] || return 2
}

__print_num_upper_case() {
	upper=ABCDEFGHIJKMLNOPQRSTUVWXYZ
	lower=abcdefghijklmnopqrstuvwxyz
	u=${1//[^$upper]} l=${1//[^$lower]}
	printf '%d' "${#u}"
}

__to-investigate-dont-use-this-function() {

	# onexit(){ while caller $((n++)); do :; done; }
	# trap onexit EXIT
	# three-fingered claw technique
	yell() { echo "$0: $*" >&2; }
	die() { yell "$*"; exit 111; }
	try() { "$@" || die "cannot $*"; }
	err() {
    	echo "Error occurred:"
    	awk 'NR>L-4 && NR<L+4 { printf "%-5d%3s%s\n",NR,(NR==L?">>>":""),$0 }' L=$1 $0
	}
	trap 'err $LINENO' EXIT
}

__oneliners-dont-use-this-function() {
	local scriptpath="$( cd "$(dirname "$0")" ; pwd -P )/" # return path, investigate symlink behavior
	VAR=$(echo ${VAR} |  sed 's/ *//g') # removes whitespace
}