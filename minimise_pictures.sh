#!/bin/sh

# convert is from imagemagick package
sourcedir=datas
targetdir=docs
mkdir -p ${targetdir}/logos
mkdir -p ${targetdir}/pictures
for d in "${sourcedir}/pictures" "${sourcedir}/logos"; do
    find $d -type f | while read pict; do
	smaller=$targetdir${pict#$sourcedir}
	if ! test -f "$smaller"; then
            convert "$pict" -define jpeg:size=300x500  -thumbnail '200x300>' -gravity center -extent 200x300 "$smaller";
	fi
    done
done

# reduce size of large image
find docs  -type f -name '*_large.png' -print | while read pict; do
    target="${pict%_large.png}.png"
    if ! test -f "${target}"; then
	convert "$pict" -quality 25 "${pict%_large.png}.png"
    fi
done