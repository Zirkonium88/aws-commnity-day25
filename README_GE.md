## Idee des CDK Sample Repos

Das CDK Sample Repo soll die Einheitlichkeit der Repos in diesem Azure-Projekt sicherstellen. Ein Pythonskript (src/setup_repo/setup_repo.py) wird einmalig beim Onboarding ausgeführt, um neben dem Klonen der Basis-App auch die Konfiguration des Repos vorzunehmen, sodass ein direktes Deployment in den GeneralPurpose- und den Development-Account möglich ist. Die Konfigurationsschritte sind:

1. Erstellung des Azure Repos im Projekt CDK-Projects.
2. Migration des Sample-Repos in das neue Repo.
3. Aufsetzen von drei Azure Pipelines:
    - azure-pipelines.yml für das Deployment in die Development-Umgebung über den Master-Branch.
    - azure-pipelines-pull-request.yml für das Mergen eines Feature-Branches in den Master-Branch.
    - azure-pipelines-release.yml für das Deployment in eine andere Umgebung per Git-Tag und via Git-Ops.
4. Aufsetzen der Branch-Policy für Pull Requests, um den Master-Branch vor direkten Änderungen zu schützen.

## Voraussetzungen

Ein Personal Access Token (PAT) muss erstellt werden Anleitung. PATs laufen standardmäßig nach 90 Tagen ab.
Außerdem muss ein SSH-Token erstellt werden Anleitung.

Die Installation einer WSL2-Distro ist abgeschlossen:

1. VSCode oder eine andere IDE installieren und Visual Studio Code WSL aktivieren.
2. Lokale Adminrechte beantragen, Hyper-V aktivieren und WSL2 auf dem Windows-PC installieren:
    - PS C:\Windows\system32> wsl --update --web-download
    - PS C:\Windows\system32> wsl --install --distribution Ubuntu-22.04 --web-download
    - Einstellungen ändern, um die Geschwindigkeit von Downloads und die Internetfähigkeit der Distro zu verbessern Anleitung.
3. Git, Python3, AWS CLI, NodeJS und das CDK in der WSL2 global installieren.

## Vorgehen

Zuerst muss ein Git-Clone in den Zielordner vorgenommen werden, der vorher erstellt wurde. Dann wird eine Python-Umgebung erstellt und aktiviert, um schließlich alle notwendigen Pakete zu installieren. Letztlich wird das Konfigurationsskript gestartet, um die Pre-Commit-Hook zu installieren, die für eine Vereinheitlichung des Codes sorgt. Dazu sind die Optionen -repo-name/rn und -pat --personal-access-token aus den Vorbereitungen zu nutzen. Im Verlauf des Skripts muss der SSH-Schlüssel eingegeben werden. Et voilà: Das DevOps-Projekt ist fertig.

```bash
mkdir -p REPO_NAME
git clone git@ssh.dev.azure.com:v3/mrh-trowe/cdk-projects/cdk-sample-repo REPO_NAME

python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pip install -r requirements-dev.txt

python3 src/setup_repo/setup_repo.py -pat "PAT" -rn "REPO_NAME"

pre-commit install
```

Danach kann die CDK-App beliebig angepasst werden. Bitte darauf achten, dass im finalen Deployment nirgendwo mehr sample steht.

## Pre-Commit Hook

Ein Pre-Commit Hook wird im Repository installiert. Dieser formatiert den Code, prüft diverse Zustände, führt Unittests durch und kompiliert die CDK-App. Erst wenn alle Prüfungen erfolgreich durchgeführt wurden, wird der Commit akzeptiert. Danach kann das Remote-Repository per git push aktualisiert werden. Die Pre-Commit Hook wird mit git add . && git commit -m "Nachricht" gestartet.

```yaml
# Snippet: .pre-commit-config.yaml
fail_fast: true
repos:
    hooks:
      - id: black
      - id: flake8
      - id: pydocstyle
      - id: pytest
      - id: cdk-synth
      - id: trailing-whitespace
      - id: check-yaml
      - id: check-added-large-files
      - id: trailing-whitespace
      - id: detect-aws-credentials
      - id: detect-private-key
```

## Verhalten der Pipeline

- Die Pipeline azure-pipelines-pull-request.yml startet nach der Erstellung eines Pull Requests und erstellt die Architektur in der Entwicklungsumgebung.
- Die Pipeline azure-pipelines.yml läuft, nachdem der Pull Request erfolgreich geschlossen wurde und erstellt ein Git-Tag.
- Die Pipeline azure-pipelines-release.yml wird manuell in der GUI mit einer Zielumgebung gestartet.

## Git Strategy

Wir nutzen einen Git-Ops-Ansatz für das Staging in andere AWS-Umgebungen. Im `./config/**`-Verzeichnis müsse *Name.json Dateine vorliegen, damit diesen enstprechend adressiert werdne können. Es ist dabei egal, ob die Umgebung im selben AWS Account liegen oder nicht.

![Git Strategy](/img/git_strategy.png)

Wenn die GUI mehr als nur zwei Deployment-Umgebungen anzeigen soll, muss die azure-pipelines-release.yml entsprechend erweitert werden:

```yaml
# Snippet

# ...
parameters:
- name: ServiceConnection
  displayName: Service Connection
  type: string
  default: mrht-general-purpose-aws-service-endpoint
  values:
    - mrht-general-purpose-aws-service-endpoint
    - --> Weitere Werte eintragen <---
- name: AwsRegion
  displayName: AWS Region
  type: string
  default: eu-central-1
- name: environmentName
  type: string
  default: generalpurpose
  values:
    - generalpurpose
    - --> Weitere Werte eintragen <--
# ...

```

Dies sind alle möglichen Service Connections:

![Service Connections](./img/service_connections.PNG)

Wenn die Umgebung aus zwei Begriffen besteht (general-purpose), muss environmentName zusammengezogen (generalpurpose) werden.

## CDK Azure DevOps Integration

Über das Repo [control-tower-cicd](https://dev.azure.com/mrh-trowe/_git/control-tower-cicd) pro AWS-Account ein Secret erzeugt, das auf einen IAM-User zeigt. Dieser User wird für die Service-Integration des CDKs mit Azure DevOps benötigt. Dieser technische User wird alle 90 Tage per Lambda rotiert. Außerdem aktualisiert die Lambda die Service-Integration in Azure DevOps per API-Token.

![CDK Azure DevOps Integration](/img/architecture.png)
