# EKS CI/CD Pipeline

Bu proje, basit bir FastAPI uygulamasının GitHub Actions kullanılarak otomatik olarak build, test ve deploy edilmesini sağlayan bir CI/CD pipeline çalışmasıdır. Pipeline içerisinde ayrıca SAST ve DAST güvenlik testleri bulunmaktadır.

## Kullanılan Teknolojiler

- FastAPI
- Docker
- GitHub Actions
- GitHub Container Registry (GHCR)
- AWS EKS
- Kubernetes
- SonarQube Cloud
- OWASP ZAP

## EKS Kurulumu

AWS üzerinde `yeni-clusterim` isimli bir EKS cluster oluşturuldu. Uygulamanın çalışması için `t3.medium` instance'lardan oluşan bir node group kullanıldı.

Cluster bağlantısı AWS CLI ile yapılandırıldı:

```bash
aws eks update-kubeconfig --region us-east-1 --name yeni-clusterim
kubectl get nodes
```

Kubernetes tarafında uygulama için Deployment ve LoadBalancer tipinde Service kullanılmaktadır. Deployment içerisinde uygulamanın iki replica'sı çalışmaktadır.

## CI/CD Pipeline

Pipeline `.github/workflows/cicd.yaml` dosyasında tanımlanmıştır ve `main` branch'e yapılan her push işleminde otomatik olarak çalışır.

Pipeline sırasıyla aşağıdaki işlemleri gerçekleştirir:

1. Repository kodunu alır.
2. SonarQube ile SAST analizi yapar.
3. Docker image oluşturur.
4. Container'ı çalıştırarak `/` ve `/health` endpointlerini test eder.
5. Docker image'ı GitHub Container Registry'ye (GHCR) gönderir.
6. AWS EKS cluster'ına bağlanır.
7. Kubernetes manifestlerini kullanarak yeni image'ı EKS'e deploy eder.
8. Deployment ve LoadBalancer'ın hazır olmasını bekler.
9. EKS üzerinde çalışan uygulamayı test eder.
10. OWASP ZAP Baseline ile çalışan uygulamaya DAST taraması gerçekleştirir.

## Deploy Akışı

```text
GitHub Push
    ↓
SonarQube SAST
    ↓
Docker Build & Test
    ↓
GHCR Push
    ↓
AWS EKS Deploy
    ↓
Kubernetes Deployment + Service
    ↓
LoadBalancer
    ↓
OWASP ZAP DAST
```

Her build sırasında Docker image, Git commit SHA değeri ile tag'lenmektedir. Böylece EKS üzerinde hangi kod sürümünün çalıştığı takip edilebilir.

Örnek:

```text
ghcr.io/kaanalkoc-gif/eks-cicd:<commit-sha>
```

## Güvenlik

Kaynak kod güvenliği için **SonarQube SAST**, deploy edilen uygulamanın dinamik güvenlik testi için ise **OWASP ZAP Baseline DAST** kullanılmaktadır.

ZAP taraması EKS üzerinde çalışan uygulamanın LoadBalancer URL'sine karşı gerçekleştirilir ve tarama sonuçları GitHub Actions üzerinden görüntülenebilir.
