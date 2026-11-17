# Harry Potter Character Interaction Network

## About the Project

This project is based on the first Harry Potter book, *Harry Potter and the Philosopher's Stone*.

The main aim of this project is to study how different characters communicate with each other in the story.

I used Python to find dialogues from the book and Gephi to create graphs showing the connections between characters.

## How I Made This Project

1. **Dialogue Collection:** I used Python to collect dialogues from the book.
2. **Finding Characters:** I tried to identify who was speaking and who they were speaking to.
3. **Creating the Network:** I made CSV files containing characters and their connections.
4. **Manual Checking:** I checked 51 dialogue records from all 17 chapters to find mistakes in the automatically collected data.
5. **Making Graphs:** I used Gephi to create two character networks.

## Improved Dialogue Sampling

I created an improved Python program called `validate_dialogues_batches.py` to select new dialogue samples without repeating previously selected records.

The program selects 3 new dialogues from each of the 17 chapters and shows how many dialogues are still available for checking.

So far, I have selected 153 dialogues in three batches:
- Batch 1: 51 dialogues (manually checked)
- Batch 2: 51 dialogues (not yet checked)
- Batch 3: 51 dialogues (not yet checked)

Out of 2,391 dialogue candidates, 2,238 are still available for future checking.

This improvement allows me to gradually check more dialogues without repeating earlier work.

## What the Graphs Show

In the graphs:

- Each circle represents a character.
- Each line represents a possible conversation between two characters.
- Bigger circles represent characters with more connections.
- Different colors show groups of connected characters.

### Graph 1: Automatically Created Network

This graph was created using the data collected by Python.

- **24 characters**
- **87 connections**

It shows the larger network, but some connections may be incorrect because they were identified automatically.

### Graph 2: Manually Checked Network

This graph was created using the dialogue records I checked myself.

- **22 characters**
- **30 different connections**
- Based on 51 manually reviewed dialogue records, including 42 direct interactions

This graph uses a smaller amount of data but includes manually checked speaker and listener information.

## What I Learned

Through this project, I learned:

- How Python can be used to collect information from a literary text.
- How to organize data using CSV files.
- How to create and understand character networks using Gephi.
- Why manually checking automatically collected data is important.
- How graphs can help us study literature in a different way.

## Tools Used

- **Python:** To collect dialogues and prepare data.
- **Excel:** To check and correct dialogue records.
- **Gephi:** To create and study character networks.
- **GitHub:** To store and share project files.

## Limitations

Python could not always correctly identify who was speaking or listening.

I manually checked only 51 dialogue records, not every dialogue in the book. Therefore, the graphs may not show every conversation accurately.

The two graphs also use different amounts of data, so they cannot be compared as if they cover exactly the same conversations.

## Conclusion

This project helped me understand how digital tools can be used to study literature. It also showed me that computers can help collect and organize information, but human checking is still important for accurate results.
