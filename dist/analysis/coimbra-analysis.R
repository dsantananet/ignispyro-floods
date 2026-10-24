# Reproducible R analysis. Base R only; no third-party R packages required.
# The fitted component is a DAILY high-flow spillway relation, not a spatial flood calibration.
options(stringsAsFactors=FALSE)
d <- read.csv('dist/data/coimbra-weir-daily.csv', na.strings=c('', 'NA'))
d$date <- as.Date(d$date)
dir.create('dist/figures', showWarnings=FALSE)
dir.create('dist/analysis', showWarnings=FALSE)
observed <- d[is.finite(d$discharged_daily_m3s) & d$discharged_daily_m3s>=0 & d$flags_present==0,]
annual <- do.call(rbind,lapply(split(observed,format(observed$date,'%Y')),function(x) data.frame(year=as.integer(format(x$date[1],'%Y')),days=nrow(x),max_daily_m3s=max(x$discharged_daily_m3s),mean_daily_m3s=mean(x$discharged_daily_m3s))))
write.csv(annual,'dist/analysis/annual-discharge.csv',row.names=FALSE)
p <- d[d$elevation_full_24h==1 & d$flags_present==0 & is.finite(d$elevation_mean_m) & is.finite(d$discharged_daily_m3s) & d$discharged_daily_m3s>=1200,]
stopifnot(nrow(p)>=7,all(p$elevation_sample_count==24))
# Event separation avoids splitting adjacent days of the same flood across train/test.
p <- p[order(p$date),]; p$event <- cumsum(c(TRUE,as.numeric(diff(p$date))>7))
p$held_out <- format(p$date,'%Y')=='2019'
stopifnot(sum(p$held_out)>=2,length(unique(p$event[!p$held_out]))>=3)
crest_m <- 14.3; width_m <- 9*15.4
p$head_m <- p$elevation_mean_m-crest_m
p$x <- width_m*p$head_m^1.5
training <- p[!p$held_out,];validation <- p[p$held_out,]
model <- lm(discharged_daily_m3s ~ 0 + x,data=training)
coefficient <- unname(coef(model)[1]);p$predicted_m3s <- coefficient*p$x
p$residual_m3s <- p$predicted_m3s-p$discharged_daily_m3s
rmse <- function(x) sqrt(mean(x^2))
p$within_training_range <- p$head_m>=min(training$head_m) & p$head_m<=max(training$head_m)
held <- p[p$held_out,]
metrics <- data.frame(coefficient_m05_s=coefficient,crest_m=crest_m,width_m=width_m,train_days=nrow(training),train_events=length(unique(training$event)),validation_days=nrow(validation),validation_events=length(unique(validation$event)),train_rmse_m3s=rmse(p$residual_m3s[!p$held_out]),validation_rmse_m3s=rmse(held$residual_m3s),validation_bias_m3s=mean(held$residual_m3s),validation_mae_m3s=mean(abs(held$residual_m3s)),head_min_m=min(training$head_m),head_max_m=max(training$head_m),observed_stage_min_m=min(p$elevation_mean_m),observed_stage_max_m=max(p$elevation_mean_m),validation_extrapolated_days=sum(validation$head_m<min(training$head_m)|validation$head_m>max(training$head_m)),operational_accepted=FALSE)
# Held-out points outside the TRAINING range are flagged, never silently accepted.
loo <- sapply(unique(training$event),function(event){q<-training[training$event!=event,];sum(q$x*q$discharged_daily_m3s)/sum(q$x^2)})
metrics$leave_event_out_coefficient_min <- min(loo);metrics$leave_event_out_coefficient_max <- max(loo)
metrics$validation_inrange_days <- sum(held$within_training_range)
metrics$validation_inrange_rmse_m3s <- if(any(held$within_training_range)) rmse(held$residual_m3s[held$within_training_range]) else NA_real_
write.csv(metrics,'dist/analysis/weir-fit-metrics.csv',row.names=FALSE)
write.csv(p,'dist/analysis/weir-fit-pairs.csv',row.names=FALSE)
theme <- function(){par(mar=c(6,4.4,3.2,1.2),col.axis='#35515c',col.lab='#173c47',col.main='#173c47',family='sans',las=1) }
png('dist/figures/09_r_historico.png',width=1500,height=750,res=150);theme();plot(annual$year,annual$max_daily_m3s,type='h',lwd=5,col=ifelse(annual$days>=330,'#087f8c','#dba85c'),xlab='Ano',ylab='Maximo medio diario descarregado (m3/s)',main='Acude-Ponte de Coimbra | arquivo SNIRH 1987-2025');abline(h=1200,lty=2,col='#a74b58');legend('topright',legend=c('>=330 dias com dados','Ano incompleto','1200 m3/s: filtro de estudo'),col=c('#087f8c','#dba85c','#a74b58'),lty=c(1,1,2),lwd=c(4,4,1),bty='n',cex=.85);dev.off()
png('dist/figures/10_r_descarga.png',width=1500,height=800,res=150);theme();plot(p$elevation_mean_m,p$discharged_daily_m3s,pch=ifelse(p$held_out,17,19),col=ifelse(p$held_out,'#ce6d42','#087f8c'),cex=1.4,xlab='Cota media diaria da albufeira (m, referencia SNIRH)',ylab='Caudal descarregado medio diario (m3/s)',main='Ajuste preliminar da descarga em cheia | 5 dias de treino + 2 de confronto');z<-seq(min(training$elevation_mean_m),max(training$elevation_mean_m),length.out=100);lines(z,coefficient*width_m*(z-crest_m)^1.5,col='#173c47',lwd=2);legend('topleft',legend=c('Treino 2001/2016','Confronto 2019','Ajuste no dominio de treino'),pch=c(19,17,NA),lty=c(NA,NA,1),col=c('#087f8c','#ce6d42','#173c47'),bty='n',cex=.9);mtext('Media diaria, nao pico instantaneo. Comportas abertas: hipotese; geometria atual e mancha nao validadas.',side=1,line=4.8,cex=.7);dev.off()
png('dist/figures/11_r_residuos.png',width=1500,height=750,res=150);theme();barplot(p$residual_m3s,names.arg=format(p$date,'%d/%m/%Y'),col=ifelse(p$held_out,'#ce6d42','#087f8c'),ylab='Estimado - publicado (m3/s)',main='Residuos do ajuste de descarga | confronto separado por evento',cex.names=.8);abline(h=0,col='#173c47');dev.off()
profile <- data.frame(distance_m=c(0,2500,4300,7200),bed_design_m=c(14.3,14.3+2500*.00019,14.3+2500*.00019+1800*.00042,14.3+2500*.00019+1800*.00042+2900*.00075))
write.csv(profile,'dist/analysis/design-profile-2010.csv',row.names=FALSE)
png('dist/figures/12_r_perfil_projeto.png',width=1500,height=750,res=150);theme();plot(profile$distance_m,profile$bed_design_m,type='o',pch=19,lwd=3,col='#087f8c',ylim=c(14,19.5),xlab='Distancia a montante do acude (m)',ylab='Cota do perfil de projeto (m)',main='Perfil de dragagem AIA2239 | projeto 2010, nao batimetria atual');abline(h=c(18,19),col=c('#3874a6','#b05a60'),lty=2);legend('topleft',legend=c('Fundo de projeto','NPA 18 m','NMC 19 m'),col=c('#087f8c','#3874a6','#b05a60'),lty=c(1,2,2),bty='n');dev.off()
writeLines(capture.output(sessionInfo()),'dist/analysis/R-sessionInfo.txt')
print(metrics)
