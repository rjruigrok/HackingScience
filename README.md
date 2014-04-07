Hacking Science - IN4253 Hacking Lab
==============
Scientists are under continuous pressure to create new scientific articles. For the purpose of this project, a semiautomated scientific article generator is created to make it trivial for any scientist to fake productivity. The idea is based on machine-generating a specific type of scientific paper, survey papers that include an overview of recent work in a single area. Related publications are collected by parsing the references of a paper. 
By recursively following citations and downloading them from the web, a large set of related publications are gathered. This collection is then used to create a new article, by including the abstracts of papers. Finally, this generation tool is enhanced with the capability of citing articles in the collection and generating a bibliography file.

## Parsing
### Paper title

### Bibliography

### Referencing papers

### Abstract

### Keywords

### Recursive parsing

## Generating
### Random titles by Markov chain

### Building up LaTeX file

### Transform LaTeX into PDF

## Web-interface
### JSON + Ajax

### Tagcloud

## Conclusion


# Future work
* The current web-interface and web-server do not have a clue about the state they are in. A small change in the Python code results in a server restart and all progress in the web-interface is lost. It would be a nice feature to save the state in some database and make the web-interface interact with this database. 
* 
