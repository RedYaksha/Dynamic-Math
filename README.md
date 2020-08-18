# Introduction
Anki is an open source flash card system that utilizes the idea of spaced-repition in their system. Usually, Anki's flashcards are static cards where there is a back and 
front side of information. These don't natively support dynamic generation of numbers, functions, etc., unless you tinker with the JavaScript yourself. This project was made to bridge
the gap between Anki's static card system and the need for randomly generated values and predetermined algorithms - along with a GUI to make it even easier for the user.

- Random Value support within an Anki card.
- Custom algorithms that the user writes will determine what the back of the card will be.
- Skip the Javascript, there's a one stop shop for all the "dynamic-cards".
- Few syntax to remember.
- Clear and understandable "Help" menu, in case you forget the syntax.
- Currently supports Real Numbers & Complex Numbers
  - Future features: Vectors, Matrices, & Functions
- Currently supports basic PEMDAS arithmetic. 
  - Future features: Derivatives, Integrals, & Symbolic Logic
  
### Motivation
I've seen much debate about the usefulness of Anki for the more "hands on" subjects such as mathematics and computer science. I personally believe that spaced repetition has it's uses
in subjects as mentioned. Yes, proofs and programming takes continuous practice to master, but, in my opinion, for the concepts and algorithms that you learn on the way, they would be more beneficial
to have in your arsenal at all times inside your long-term memory, rather than being forgetten as time passes. This is definitely still up for debate, but I wanted to experiment with
this in my own educational journey which led to the making of this tool.
