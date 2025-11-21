# About

Work-in-progress software for generating scorecards for World Cube Association (WCA) competitions. Please read the warning below.

# A warning

> Perfect is the enemy of good.

*Aphorism*

This repository is a work-in-progress. It's messy, it's not very user-friendly, there's absurdly platform-dependent code, and there are a grand total of 121 TODOs. If you don't have a decent programming background, I wouldn't recommend touching it. The only reason it's on GitHub is so other delegates in my region don't have to use mail merge.

As it stands, I'm aware of at least one reason this will not work outside of Windows Subsystem for Linux (no, I'm not kidding), and I haven't bothered to check whether there are any other platform-specific issues.

You have been warned.

# Tutorial

## Setup/environment details

Unfortunately, I haven't put a lot of effort into platform independence yet.

1. **Python version**: This was developed using Python 3.10.12. Hopefully other Python versions work.
2. **EDITME.py**: I run this in WSL (Windows Subsystem for Linux). I haven't tested this on any other platform. If you're not using WSL, you will, at the very least, need to edit `pdf_gen/EDITME.py` so the PDF generation scripts use the correct font paths. (Isn't this fun?)
3. **Python packages**: Run `pip install -r requirements.txt`. Please let David know if this doesn't work.

## Using the scripts

1. Find the competition ID, which comes at the end of the competition website's URL. For example, for https://www.worldcubeassociation.org/competitions/WesternChampionship2025, the competition ID is WesternChampionship2025. For the rest of this tutorial, we'll use CompId to refer to your competition ID.

2. Generate the options XLSX with this command: `./options_gen/options_gen.py CompId`. This will generate a spreadsheet at `Options/Options_CompId.xlsx`, which you can use to configure the PDFs that are generated later.

3. Edit the spreadsheet at `Options/Options_CompId.xlsx` using your favorite compatible spreadsheet editor (ideally Microsoft Excel). Choose your options using the "Value" column. Be careful not to change anything else or you'll likely break things.

4. Generate the scorecard PDFs with this command: `./scorecard_gen.py CompId`. This will generate PDFs in the "Scorecards" directory. Please double-check your work.
