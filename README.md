# SciModeler Dashboard
This is the dashboard we build by Dash library of python. 

Following will be the steps how you should use our dashboard.

1. Before staring with the dashboard, you need Neo4j. Download the Neo4j desktop if you don't have it yet(https://neo4j.com/download/).

2. In Neo4j, creat a new project with a local DMBS, add the .cypher files from annotated articles as the database. When you creating the local DMBS, you need set a password,
and this password will be used for later.

3. Running the DMBS, go to Neo4j Browser->Project Files, click all the start button for the .cypher files. Then you should see the Neo4j says you are  
connected as user neo4j to bolt://localhost:7687

4. In the python code, change the username and password in the auth parameter in the graph.run function to your own username and password of neo4j.

5. Run the python code file on your jupterhub, you need to install the libraries that are used in the python code(!pip install py2neo to install py2neo library for example).

6. In the output you will see the address of the localhost of our dashboard, click it to open a new webpage and welcome to our dashboard!

7. For how to use the dashboard, please refers to our manual. 

# Authors
Martijn van Veldhuizen – Secretary

Michelle van Alst – Secretary (chair)

Nelson van Duin – Technical Lead 

Rafaël Tulen – Data Steward 

Robert Xu - Controller 
