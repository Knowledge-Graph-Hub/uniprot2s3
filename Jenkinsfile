pipeline {
    agent {
        docker {
            reuseNode false
            image 'caufieldjh/kg-idg:4'
        }
    }
    //triggers{
    //    cron('H H 1 1-12 *')
    //}
    environment {
        BUILDSTARTDATE = sh(script: "echo `date +%Y%m%d`", returnStdout: true).trim()
        S3PROJECTDIR = '' // no trailing slash

        // Distribution ID for the AWS CloudFront for this bucket
        // used solely for invalidations
        AWS_CLOUDFRONT_DISTRIBUTION_ID = 'EUVSWXZQBXCFP'
    }
    options {
        timestamps()
        disableConcurrentBuilds()
    }
    stages {
        stage('Ready and clean') {
            steps {
                // Give us a minute to cancel if we want.
                sleep time: 30, unit: 'SECONDS'
            }
        }

        stage('Initialize') {
            steps {
                // print some info
                dir('./working') {
                    sh 'env > env.txt'
                    sh 'echo $BRANCH_NAME > branch.txt'
                    sh 'echo "$BRANCH_NAME"'
                    sh 'cat env.txt'
                    sh 'cat branch.txt'
                    sh "echo $BUILDSTARTDATE"
                    sh "python3.9 --version"
                    sh "id"
                    sh "whoami" // this should be jenkinsuser
                    sh "pwd"
                    sh "ls -l"
                    // if the above fails, then the docker host didn't start the docker
                    // container as a user that this image knows about. This will
                    // likely cause lots of problems (like trying to write to $HOME
                    // directory that doesn't exist, etc), so we should fail here and
                    // have the user fix this

                }
            }
        }

        stage('Setup') {
            steps {
                dir('./gitrepo') {
                    git(
                            url: 'https://github.com/Knowledge-Graph-Hub/uniprot2s3',
                            branch: env.BRANCH_NAME
                    )
            sh '/usr/bin/python3.9 -m venv venv'
			sh '. venv/bin/activate'
            // sh './venv/bin/pip install .'
            sh 'pwd'
			sh './venv/bin/pip install s3cmd'
                }
            }
        }

        stage('Run downloader') {
            steps {
                dir('./gitrepo') {
                    sh '. venv/bin/activate && rm -f data/raw/uniprot_empty_organism.tsv || true'
		            sh '. venv/bin/activate && make all'
                }
            }
        }

        // Harry to help here
        stage('Upload result') {
            // Store similarity results at s3://kg-hub-public-data/frozen_incoming_data/uniprot
            steps {
                dir('./gitrepo') {
                    script {
                            withCredentials([
					            file(credentialsId: 's3cmd_kg_hub_push_configuration', variable: 'S3CMD_CFG'),
					            file(credentialsId: 'aws_kg_hub_push_json', variable: 'AWS_JSON'),
					            string(credentialsId: 'aws_kg_hub_access_key', variable: 'AWS_ACCESS_KEY_ID'),
					            string(credentialsId: 'aws_kg_hub_secret_key', variable: 'AWS_SECRET_ACCESS_KEY')]) {


                                // upload to remote
				sh 'tar -czvf uniprot_proteomes.tar.gz ./data/raw/s3'
                                sh '. venv/bin/activate && s3cmd -c $S3CMD_CFG put -pr --acl-public --cf-invalidate uniprot_proteomes.tar.gz s3://kg-hub-public-data/frozen_incoming_data/uniprot/'
                                // Should now appear at:
                                // https://kg-hub.berkeleybop.io/frozen_incoming_data/uniprot
                            }

                        }
                    }
                }
            }
        }

    post {
        always {
            echo 'In always'
            echo 'Cleaning workspace...'
            cleanWs()
        }
        success {
            echo 'I succeeded!'
        }
        unstable {
            echo 'I am unstable :/'
        }
        failure {
            echo 'I failed :('
        }
        changed {
            echo 'Things were different before...'
        }
    }
}
