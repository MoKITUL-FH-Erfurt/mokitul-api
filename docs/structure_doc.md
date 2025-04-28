# Application ReadMe

## Overview

This document provides an overview of the application structure, including details about the database, vector database, use cases, and API layer. Please note that the layer models are not separated at the moment.

## Table of Contents

1. [Application Structure](#application-structure)
2. [Database](#database)
3. [Vector Database](#vector-database)
4. [Use Cases](#use-cases)
5. [API Layer](#api-layer)
6. [Future Improvements](#future-improvements)

## Application Structure

The application is organized into several key components:

- **Database**: Manages the storage and retrieval of structured data.
- **Vector Database**: Handles the storage and querying of vectorized data.
- **Use Cases**: Defines the business logic and operations that the application supports.
- **API Layer**: Exposes the functionality of the application through a set of endpoints.

### Note
Currently, the layer models are not separated, meaning that the business logic, data access, and API handling are not distinctly modularized.

## Database

The database is responsible for storing and managing structured data.
It includes tables for various entities such as users, products, orders, etc.
The database is implemented using MongoDB.

We only have one enitity at the moment, which is the conversation.

## Vector Database

The vector database is used for storing and querying vectorized data.
We use Qdrant as our vector database.
With Hybrid Search, we can combine vector search with traditional keyword search.

The dens retrievel model can be customized, but the sparse model is fix at the moment.
We use for sparse retrival at the moment naver/efficient-splade-VI-BT-large.
This is the default model used by llama index for the implementation of the hybrid search.


## Use Cases
- **Conversation Usecases** contains all interactions with an user conversation
- **Moodle Usecases** contains all interactions with the Moodle API
- **Vector Usecases** contains all interactions with the vector database
- **RAGLMM Usecase** contains Request agains LLM with document retrieval

## API Layer

## Future Improvements

To enhance the maintainability and scalability of the application, the following improvements are planned:

- **Separation of Layer Models**: Modularize the application by separating the business logic, data access, and API handling into distinct layers.
- **Enhanced Security**: Implement additional security measures such as input validation.
---
