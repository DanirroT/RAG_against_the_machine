#!/bin/bash

if [ -z "$1" ]; then
    COMMIT_MESSAGE="$(date +%m/%d)"
    echo "
No commit message, using ${COMMIT_MESSAGE}
"
else
    COMMIT_MESSAGE="$1"
fi

make fclean
make clean
echo ""
git status
echo ""
git add .
echo ""
git status
echo ""
git commit -m "${COMMIT_MESSAGE}"
echo ""
if [ $? -ne 0 ]; then
    echo "Warning: Commit failed or there were no changes to commit."
    exit 0
fi
git push
echo ""
if [ $? -eq 0 ]; then
    echo " --- Successful Push ---"
else
    echo " --- Error: Push failed. ---"
fi
echo ""
