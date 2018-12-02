# Search Engine for Wikipedia Dumps

`index.py` - builds the index file
`search.py` - searches over the built index

index is built in the `index` directory.

## Index Building
The entire corpus is gone over and each page in the index is index. Due to the size of the dump it is not possible to store the entire 
dump's data in memory and so multiple partial indices are written. These are all merged into a final file ('./index/index') using a multiway
heap based merge.
Otherfiles like offset and titles are made to help during search time

### Code Execution

`python3 index.py <path-to-wikidump-file>`

`python3 search.py`
