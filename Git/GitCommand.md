# To create git
git init (initiate at the project level)
git add . (add all file in project)
git commit -m "Message" (start to commit with message as comment for the commit)
# To check versions history
git log --oneline (show each commit as one line)
# To return the state to a version
git reset --hard HEAD (return everything back to the latest version)
git reset --hard xxxxx (return to a specific version)
# To show all curernt file:
git ls-tree -r HEAD --name-only
# TO show status of git in files:
git status
# To see current file in git in simple way
git ls-tree -r HEAD --name-only