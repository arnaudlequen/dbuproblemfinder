# Parameterized Problem Finder

### Usage
Start the solver. You can load it directly with a file containing a parameterized problem class.
```shell script
python3 solver.py [-f filename]
```

Commands:
 * **init** *[guided]* - Initialize a parameterized problem. Add option "guided" for help with the syntax
 * **add** *tractable|intractable|reduction* - Specify the tractability of a problem, or add a known reduction. You will be prompted the problem or reduction to add.
 * **solve** *tractable|intractable [params]* - Check if a problem's tractability is known or can be deduced
 * **saturate** - Try to solve as many problems are possible, and register them in the database
 * **open** *[impact]* - Show all open problems, and the consequences of solving them if option "impact" is specified
 * **impact** *[id|[params..]]* - Shows which problems would be solved by solving another problem. If command open impact was run before, the id of the problem can be specified.
 Otherwise, a list of parameters can be given"
 * **save** *filename* - Save the current state in a file
 * **load** *filename* - Load a parameterized problem
 
Format:
 * *[params]* - List of parameters, with whitespace " " as separator
 * *[reduction]* - List of parameters separated by character ">"
 
### Example
```shell script
> python3 solver.py
Parameterized problem finder v0.0.1
> load DBU.json
Successfully loaded file DBU.json
> add reduction
> a c p > a c p e
Successfully added reduction
> solve tractable a c p u
Solution found:
-> {a, c, p, u}-DBU
-> {a, c, e, p, u}-DBU
-> {e, u}-DBU
Register the problem as a known tractable problem? Y/n
> 
Successfully registered {a, c, p, u} as a known tractable problem
> solve intractable a f o p
Solution found:
-> {a, f, o, p, u}-DBU
-> {a, f, o, p}-DBU
```