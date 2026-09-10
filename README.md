## Final architecture: 
                            ┌───────────────────────┐
                            │       INTERNET        │
                            │       End Users       │
                            └───────────┬───────────┘
                                        │
                                        │ HTTP / HTTPS
                                        ▼
                         ┌─────────────────────────────┐
                         │       APPLICATION LB        │
                         │       Internet-facing       │
                         └─────────────┬───────────────┘
                                       │
                        ┌──────────────┴──────────────┐
                        │                             │
                        ▼                             ▼
                ┌───────────────┐             ┌───────────────┐
                │ Public Subnet │             │ Public Subnet │
                │     AZ-A      │             │     AZ-B      │
                │               │             │               │
                │     ALB       │             │     ALB       │
                └───────┬───────┘             └───────┬───────┘
                        │                             │
                        └──────────────┬──────────────┘
                                       │
                                       ▼
                ╔════════════════════════════════════════════╗
                ║              PRIVATE SUBNETS              ║
                ║                                            ║
                ║   AZ-A                         AZ-B        ║
                ║ ┌────────────────┐       ┌────────────────┐║
                ║ │ Frontend ECS   │       │ Frontend ECS   │║
                ║ │ Task           │       │ Task           │║
                ║ └───────┬────────┘       └───────┬────────┘║
                ║         │                        │         ║
                ║         └──────────┬─────────────┘         ║
                ║                    ▼                       ║
                ║         ┌─────────────────────┐            ║
                ║         │ Backend ECS Service │            ║
                ║         │                     │            ║
                ║         │ Task A    Task B    │            ║
                ║         └──────────┬──────────┘            ║
                ╚════════════════════╪═══════════════════════╝
                                     │
                      ┌──────────────┼──────────────┐
                      │              │              │
                      ▼              ▼              ▼
                  DynamoDB           S3        CloudWatch
                      │
                      │
               VPC Endpoints
                      │
                      ▼
               AWS Private Network

## Key Idea:
          Internet
           │
           ▼
         ALB
           │
           ▼
        Private ECS
           │
           ├── Backend
           │
           └── AWS Services
           
## Networking Diagram:
                                      AWS VPC
                                   10.0.0.0/16
                                        │
                     ┌──────────────────┴──────────────────┐
                     │                                     │
                     ▼                                     ▼
                Availability Zone A                  Availability Zone B
                     │                                     │
             ┌───────┴────────┐                    ┌───────┴────────┐
             │                │                    │                │
             ▼                ▼                    ▼                ▼
        ┌───────────┐   ┌─────────────┐      ┌───────────┐   ┌─────────────┐
        │  Public   │   │   Private   │      │  Public   │   │   Private   │
        │  Subnet A │   │   Subnet A  │      │  Subnet B │   │   Subnet B  │
        │           │   │             │      │           │   │             │
        │   ALB     │   │ ECS Tasks   │      │   ALB     │   │ ECS Tasks   │
        └─────┬─────┘   └─────────────┘      └─────┬─────┘   └─────────────┘
              │                                     │
              └────────────────┬────────────────────┘
                               │
                               ▼
                       Internet Gateway
                               │
                               ▼
                           INTERNET

## Deployment Flow
                         ┌──────────────┐
                         │    GitHub    │
                         └──────┬───────┘
                                │
                                ▼
                       ┌─────────────────┐
                       │  CodePipeline  │
                       └────────┬────────┘
                                │
                                ▼
                       ┌─────────────────┐
                       │   CodeBuild     │
                       │                 │
                       │ Test            │
                       │ Docker Build    │
                       │ Push to ECR     │
                       └────────┬────────┘
                                │
                                ▼
                         ┌────────────┐
                         │    ECR     │
                         └─────┬──────┘
                               │
                               ▼
                     ┌──────────────────┐
                     │ ECS Deployment   │
                     └────────┬─────────┘
                              │
                 ┌────────────┴────────────┐
                 │                         │
                 ▼                         ▼
          Frontend Service          Backend Service
                 │                         │
                 └────────────┬────────────┘
                              │
                              ▼
                             ALB
                              │
                              ▼
                          INTERNET
